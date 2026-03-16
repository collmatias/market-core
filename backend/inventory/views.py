from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from rest_framework import viewsets

# 🌟 IMPORTACIÓN CORREGIDA: Traemos el patovica desde la app 'core'
from core.decorators import admin_requerido 

from .models import Producto, MovimientoStock
from .serializers import ProductoSerializer, MovimientoStockSerializer
from .forms import ProductoForm, MovimientoStockForm

# --- API ---
class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all().order_by('descripcion')
    serializer_class = ProductoSerializer

class MovimientoStockViewSet(viewsets.ModelViewSet):
    queryset = MovimientoStock.objects.all().order_by('-fecha')
    serializer_class = MovimientoStockSerializer

# --- FRONTEND ---

@login_required
def lista_productos(request):
    query = request.GET.get('q')
    if query:
        productos = Producto.objects.filter(
            Q(descripcion__icontains=query) | Q(codigo_barras__icontains=query)
        ).order_by('descripcion')
    else:
        productos = Producto.objects.all().order_by('descripcion')
        
    return render(request, 'inventory/lista_productos.html', {'productos': productos})

# 🌟 LÍNEA RESTAURADA: Faltaba el 'def crear_producto(request):'
@login_required
@admin_requerido
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto creado exitosamente.")
            return redirect('lista_productos')
    else:
        form = ProductoForm()
    return render(request, 'inventory/producto_form.html', {'form': form})

# 🔒 NUEVA VISTA: EDITAR (Solo Admin)
@login_required
@admin_requerido
def editar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto actualizado.")
            return redirect('lista_productos')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'inventory/producto_form.html', {'form': form})

# 🔒 NUEVA VISTA: ELIMINAR (Solo Admin)
@login_required
@admin_requerido
def eliminar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    producto.delete()
    messages.success(request, "Producto eliminado del sistema.")
    return redirect('lista_productos')


# 🌟 MAGIA CONTABLE: Control de Entradas y Salidas
@login_required
def registrar_movimiento(request):
    # Verificamos si es ADMIN
    es_admin = request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.es_admin)

    if request.method == 'POST':
        form = MovimientoStockForm(request.POST)
        if form.is_valid():
            movimiento = form.save(commit=False)
            
            # 🛡️ DEFENSA ACTIVA: Usamos 'tipo' en lugar de 'tipo_movimiento'
            if not es_admin and movimiento.tipo != 'ENTRADA':
                messages.error(request, "Operación denegada. Solo los Administradores pueden retirar stock manualmente.")
                return redirect('lista_productos')

            movimiento.usuario = request.user
            movimiento.save()
            messages.success(request, "Movimiento de stock registrado.")
            return redirect('lista_productos')
    else:
        form = MovimientoStockForm()
        
        # 🎨 DEFENSA VISUAL: Restringimos las opciones del selector 'tipo'
        if not es_admin:
            form.fields['tipo'].choices = [('ENTRADA', 'Ingreso de Mercadería')]

    return render(request, 'inventory/movimiento_form.html', {'form': form})