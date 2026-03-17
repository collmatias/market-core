import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Sum, Count
from django.utils import timezone
from django.utils.translation import gettext as _
from django.contrib.auth.decorators import login_required
from datetime import datetime, time

from .models import Sale, SaleItem
from inventory.models import Product
from core.models import Client


@login_required
def new_sale(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                client_id = request.POST.get("client")
                payment_method = request.POST.get("payment_method")
                cart_json = request.POST.get("cart_data")
                cart = json.loads(cart_json)

                if not cart:
                    messages.error(request, _("Cart is empty."))
                    return redirect("new_sale")

                sale = Sale.objects.create(
                    company=request.user.profile.company,
                    client_id=client_id if client_id else None,
                    payment_method=payment_method,
                    total=0
                )

                running_total = 0
                for item in cart:
                    product = Product.objects.get(id=item["id"])
                    quantity = int(item["quantity"])
                    price = float(item["price"])
                    subtotal = quantity * price
                    running_total += subtotal

                    SaleItem.objects.create(
                        sale=sale,
                        product=product,
                        quantity=quantity,
                        unit_price=price,
                        subtotal=subtotal
                    )

                sale.total = running_total
                sale.save()
                messages.success(request, _("Sale #%(id)s registered successfully.") % {"id": sale.id})
                return redirect("sale_detail", sale_id=sale.id)

        except Exception as e:
            messages.error(request, _("Error processing sale: %(error)s") % {"error": str(e)})
            return redirect("new_sale")

    products = Product.objects.filter(company=request.user.profile.company).order_by("description")
    clients = Client.objects.filter(company=request.user.profile.company).order_by("last_name")

    return render(request, "sales/new_sale.html", {
        "products": products,
        "clients": clients
    })


@login_required
def sale_list(request):
    sales_qs = Sale.objects.filter(
        company=request.user.profile.company
    ).select_related("client").order_by("-date")
    paginator = Paginator(sales_qs, 25)
    page = request.GET.get("page")
    sales = paginator.get_page(page)
    return render(request, "sales/sale_list.html", {"sales": sales})


@login_required
def sale_detail(request, sale_id):
    sale = get_object_or_404(Sale, pk=sale_id, company=request.user.profile.company)
    return render(request, "sales/sale_detail.html", {"sale": sale})


@login_required
def cash_report(request):
    date_str = request.GET.get("date")
    shift = request.GET.get("shift", "all")

    if date_str:
        try:
            filter_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            filter_date = timezone.now().date()
    else:
        filter_date = timezone.now().date()

    sales = Sale.objects.filter(company=request.user.profile.company, date__date=filter_date)

    if shift == "morning":
        sales = sales.filter(date__time__lt=time(14, 0))
    elif shift == "afternoon":
        sales = sales.filter(date__time__gte=time(14, 0))

    grand_total = sales.aggregate(Sum("total"))["total__sum"] or 0

    payment_breakdown = sales.values("payment_method").annotate(
        count=Count("id"),
        total=Sum("total")
    ).order_by("payment_method")

    return render(request, "sales/cash_report.html", {
        "sales": sales.order_by("-date"),
        "grand_total": grand_total,
        "breakdown": payment_breakdown,
        "selected_date": filter_date,
        "selected_shift": shift
    })
