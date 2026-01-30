# Create your views here.
from rest_framework import viewsets
from .models import Producto, MovimientoStock
from .serializers import ProductoSerializer, MovimientoStockSerializer

from django.shortcuts import render, redirect
from django.db.models import Q
from .models import Producto, MovimientoStock
from .forms import ProductoForm, MovimientoStockForm


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all().order_by('descripcion')
    serializer_class = ProductoSerializer

class MovimientoStockViewSet(viewsets.ModelViewSet):
    queryset = MovimientoStock.objects.all().order_by('-fecha')
    serializer_class = MovimientoStockSerializer


def lista_productos(request):
    # Filtro simple por si quieres buscar
    query = request.GET.get('q')
    if query:
        productos = Producto.objects.filter(
            Q(descripcion__icontains=query) | Q(codigo_barras__icontains=query)
        ).order_by('descripcion')
    else:
        productos = Producto.objects.all().order_by('descripcion')
        
    return render(request, 'inventory/lista_productos.html', {'productos': productos})

def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_productos')
    else:
        form = ProductoForm()
    return render(request, 'inventory/producto_form.html', {'form': form})

def registrar_movimiento(request):
    if request.method == 'POST':
        form = MovimientoStockForm(request.POST)
        if form.is_valid():
            # Asignamos el usuario que está logueado
            movimiento = form.save(commit=False)
            movimiento.usuario = request.user
            movimiento.save()
            return redirect('lista_productos')
    else:
        form = MovimientoStockForm()
    return render(request, 'inventory/movimiento_form.html', {'form': form})