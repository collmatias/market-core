from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.translation import gettext as _
from rest_framework import viewsets

from core.decorators import admin_required

from .models import Product, StockMovement
from .serializers import ProductSerializer, StockMovementSerializer
from .forms import ProductForm, StockMovementForm


# --- API ---
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.filter(
            company=self.request.user.profile.company
        ).order_by("description")


class StockMovementViewSet(viewsets.ModelViewSet):
    serializer_class = StockMovementSerializer

    def get_queryset(self):
        return StockMovement.objects.filter(
            product__company=self.request.user.profile.company
        ).order_by("-date")


# --- FRONTEND ---

@login_required
def product_list(request):
    query = request.GET.get("q")
    qs = Product.objects.for_company(request.user)
    if query:
        qs = qs.filter(
            Q(description__icontains=query) | Q(barcode__icontains=query)
        )
    products_qs = qs.order_by("description")
    paginator = Paginator(products_qs, 25)
    page = request.GET.get("page")
    products = paginator.get_page(page)
    return render(request, "inventory/product_list.html", {"products": products})


@login_required
@admin_required
def create_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.company = request.user.profile.company
            product.save()
            messages.success(request, _("Product created successfully."))
            return redirect("product_list")
    else:
        form = ProductForm()
    return render(request, "inventory/product_form.html", {"form": form})


@login_required
@admin_required
def edit_product(request, id):
    product = get_object_or_404(Product, id=id, company=request.user.profile.company)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, _("Product updated."))
            return redirect("product_list")
    else:
        form = ProductForm(instance=product)
    return render(request, "inventory/product_form.html", {"form": form})


@login_required
@admin_required
def delete_product(request, id):
    if request.method != "POST":
        return redirect("product_list")
    product = get_object_or_404(Product, id=id, company=request.user.profile.company)
    product.delete()
    messages.success(request, _("Product deleted."))
    return redirect("product_list")


@login_required
def register_movement(request):
    is_admin = request.user.is_superuser or (hasattr(request.user, "profile") and request.user.profile.is_admin)

    if request.method == "POST":
        form = StockMovementForm(request.POST, company=request.user.profile.company)
        if form.is_valid():
            movement = form.save(commit=False)
            if not is_admin and movement.type != "IN":
                messages.error(request, _("Operation denied. Only administrators can withdraw stock."))
                return redirect("product_list")
            movement.user = request.user
            movement.save()
            messages.success(request, _("Stock movement recorded."))
            return redirect("product_list")
    else:
        form = StockMovementForm(company=request.user.profile.company)
        if not is_admin:
            form.fields["type"].choices = [("IN", _("Incoming Stock"))]

    return render(request, "inventory/movement_form.html", {"form": form})


@login_required
def product_labels(request):
    ids = request.GET.getlist("ids")
    company = request.user.profile.company

    if ids:
        products = Product.objects.filter(company=company, id__in=ids).order_by("description")
    else:
        products = Product.objects.filter(company=company).exclude(
            barcode__isnull=True
        ).exclude(barcode="").order_by("description")

    return render(request, "inventory/product_labels.html", {"products": products})
