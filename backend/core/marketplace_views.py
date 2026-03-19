"""
Marketplace views — Supplier portal + Vet browsing + Order management.

Suppliers: manage their product listings, track order status
Vets: browse suppliers, place orders, track order status
"""
import json
import logging

import requests as http_requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

from core.models import Company

logger = logging.getLogger(__name__)


def _cloud_api_url():
    return settings.CLOUD_API_URL


def _get_tenant_token(company):
    """Get or refresh the tenant JWT for this company."""
    if company.cloud_tenant_token:
        return company.cloud_tenant_token
    # Try to get a fresh token
    if not company.email or not company.cloud_tenant_id:
        return None
    try:
        resp = http_requests.post(
            f"{_cloud_api_url()}/tenant/token",
            json={"email": company.email, "api_secret": settings.CLOUD_API_SECRET},
            timeout=5,
        )
        if resp.status_code == 200:
            token = resp.json().get("token")
            company.cloud_tenant_token = token
            company.save(update_fields=["cloud_tenant_token"])
            return token
    except Exception as e:
        logger.warning("Failed to get tenant token: %s", e)
    return None


def _cloud_headers(company):
    token = _get_tenant_token(company)
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}


# === SUPPLIER PORTAL ===

@login_required
def supplier_dashboard(request):
    """Supplier dashboard — product listing overview."""
    company = request.user.profile.company
    if company.account_type != 'SUPPLIER':
        messages.error(request, _("This section is for suppliers only."))
        return redirect("home")

    products = []
    headers = _cloud_headers(company)
    if headers:
        try:
            resp = http_requests.get(
                f"{_cloud_api_url()}/supplier/products",
                headers=headers, timeout=5,
            )
            if resp.status_code == 200:
                products = resp.json()
        except Exception as e:
            logger.warning("Failed to load supplier products: %s", e)

    return render(request, "marketplace/supplier_dashboard.html", {
        "products": products,
    })


@login_required
def supplier_product_add(request):
    """Add a product to the supplier's cloud catalog."""
    company = request.user.profile.company
    if company.account_type != 'SUPPLIER':
        return redirect("home")

    if request.method == "POST":
        headers = _cloud_headers(company)
        if not headers:
            messages.error(request, _("Cloud API connection error."))
            return redirect("supplier_dashboard")

        data = {
            "description": request.POST.get("description", "").strip(),
            "sku": request.POST.get("sku", "").strip() or None,
            "ean": request.POST.get("ean", "").strip() or None,
            "brand": request.POST.get("brand", "").strip() or None,
            "category": request.POST.get("category", "").strip() or None,
            "unit_price": float(request.POST.get("unit_price", 0)),
            "stock_available": int(request.POST.get("stock_available", 0)),
        }
        try:
            resp = http_requests.post(
                f"{_cloud_api_url()}/supplier/products",
                headers=headers, json=data, timeout=5,
            )
            if resp.status_code == 201:
                messages.success(request, _("Product listed successfully."))
                return redirect("supplier_dashboard")
            else:
                messages.error(request, _("Error: %(detail)s") % {"detail": resp.text})
        except Exception as e:
            messages.error(request, _("Cloud API connection error."))

    return render(request, "marketplace/supplier_product_form.html")


@login_required
def supplier_product_edit(request, product_id):
    """Edit a supplier product."""
    company = request.user.profile.company
    headers = _cloud_headers(company)
    if not headers:
        messages.error(request, _("Cloud API connection error."))
        return redirect("supplier_dashboard")

    if request.method == "POST":
        data = {
            "description": request.POST.get("description", "").strip(),
            "unit_price": float(request.POST.get("unit_price", 0)),
            "stock_available": int(request.POST.get("stock_available", 0)),
            "brand": request.POST.get("brand", "").strip() or None,
            "category": request.POST.get("category", "").strip() or None,
        }
        try:
            resp = http_requests.patch(
                f"{_cloud_api_url()}/supplier/products/{product_id}",
                headers=headers, json=data, timeout=5,
            )
            if resp.status_code == 200:
                messages.success(request, _("Product updated."))
                return redirect("supplier_dashboard")
        except Exception:
            pass
        messages.error(request, _("Error updating product."))

    return redirect("supplier_dashboard")


@login_required
def supplier_product_delete(request, product_id):
    """Deactivate a supplier product."""
    if request.method != "POST":
        return redirect("supplier_dashboard")

    company = request.user.profile.company
    headers = _cloud_headers(company)
    if headers:
        try:
            http_requests.delete(
                f"{_cloud_api_url()}/supplier/products/{product_id}",
                headers=headers, timeout=5,
            )
            messages.success(request, _("Product removed from marketplace."))
        except Exception:
            messages.error(request, _("Error removing product."))

    return redirect("supplier_dashboard")


# === VET MARKETPLACE BROWSING ===

@login_required
def marketplace_search(request):
    """Browse supplier products (for vets)."""
    q = request.GET.get("q", "").strip()
    region = request.GET.get("region", "").strip() or None
    results = []

    if q and len(q) >= 2:
        try:
            params = {"q": q, "limit": 50}
            if region:
                params["region"] = region
            resp = http_requests.get(
                f"{_cloud_api_url()}/supplier/search",
                params=params, timeout=5,
            )
            if resp.status_code == 200:
                results = resp.json().get("results", [])
        except Exception as e:
            logger.warning("Marketplace search failed: %s", e)

    return render(request, "marketplace/search.html", {
        "query": q,
        "region": region,
        "results": results,
    })


# === ORDERS ===

@login_required
def order_list(request):
    """List orders (buyer or supplier view)."""
    company = request.user.profile.company
    headers = _cloud_headers(company)
    if not headers:
        messages.error(request, _("Cloud API connection error."))
        return redirect("home")

    is_supplier = company.account_type == 'SUPPLIER'
    role = request.GET.get("role", "buyer")
    status_filter = request.GET.get("status", "")

    params = {"role": role}
    if status_filter:
        params["status"] = status_filter

    orders = []
    try:
        resp = http_requests.get(
            f"{_cloud_api_url()}/orders/my",
            headers=headers, params=params, timeout=5,
        )
        if resp.status_code == 200:
            orders = resp.json()
    except Exception as e:
        logger.warning("Failed to load orders: %s", e)

    return render(request, "marketplace/order_list.html", {
        "orders": orders,
        "role": role,
        "status_filter": status_filter,
        "is_supplier": is_supplier,
    })


@login_required
def order_detail(request, order_id):
    """View order details."""
    company = request.user.profile.company
    headers = _cloud_headers(company)
    if not headers:
        messages.error(request, _("Cloud API connection error."))
        return redirect("order_list")

    order = None
    try:
        resp = http_requests.get(
            f"{_cloud_api_url()}/orders/{order_id}",
            headers=headers, timeout=5,
        )
        if resp.status_code == 200:
            order = resp.json()
    except Exception:
        pass

    if not order:
        messages.error(request, _("Order not found."))
        return redirect("order_list")

    is_buyer = order.get("buyer_tenant_id") == company.cloud_tenant_id
    is_supplier_order = order.get("supplier_tenant_id") == company.cloud_tenant_id

    return render(request, "marketplace/order_detail.html", {
        "order": order,
        "is_buyer": is_buyer,
        "is_supplier": is_supplier_order,
    })


@login_required
def order_action(request, order_id, action):
    """Perform an order state transition."""
    if request.method != "POST":
        return redirect("order_detail", order_id=order_id)

    company = request.user.profile.company
    headers = _cloud_headers(company)
    if not headers:
        messages.error(request, _("Cloud API connection error."))
        return redirect("order_detail", order_id=order_id)

    allowed_actions = {"place", "accept", "ship", "deliver", "cancel"}
    if action not in allowed_actions:
        messages.error(request, _("Invalid action."))
        return redirect("order_detail", order_id=order_id)

    try:
        data = {}
        if action == "quote":
            data = {
                "quoted_total": float(request.POST.get("quoted_total", 0)),
                "supplier_notes": request.POST.get("supplier_notes", ""),
            }

        resp = http_requests.post(
            f"{_cloud_api_url()}/orders/{order_id}/{action}",
            headers=headers, json=data if data else None, timeout=5,
        )
        if resp.status_code == 200:
            messages.success(request, _("Order updated."))
        else:
            detail = resp.json().get("detail", resp.text)
            messages.error(request, _("Error: %(detail)s") % {"detail": detail})
    except Exception as e:
        messages.error(request, _("Cloud API connection error."))

    return redirect("order_detail", order_id=order_id)


@login_required
def order_quote(request, order_id):
    """Supplier quotes an order."""
    if request.method != "POST":
        return redirect("order_detail", order_id=order_id)

    company = request.user.profile.company
    headers = _cloud_headers(company)
    if not headers:
        messages.error(request, _("Cloud API connection error."))
        return redirect("order_detail", order_id=order_id)

    data = {
        "quoted_total": float(request.POST.get("quoted_total", 0)),
        "supplier_notes": request.POST.get("supplier_notes", ""),
        "items": [],
    }

    try:
        resp = http_requests.post(
            f"{_cloud_api_url()}/orders/{order_id}/quote",
            headers=headers, json=data, timeout=5,
        )
        if resp.status_code == 200:
            messages.success(request, _("Quote sent."))
        else:
            detail = resp.json().get("detail", resp.text)
            messages.error(request, _("Error: %(detail)s") % {"detail": detail})
    except Exception:
        messages.error(request, _("Cloud API connection error."))

    return redirect("order_detail", order_id=order_id)
