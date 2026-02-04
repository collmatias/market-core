import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth.decorators import login_required # <--- EL CANDADO
from django.db.models import Sum, Count

from .models import Venta, DetalleVenta
from inventory.models import Producto
from core.models import Cliente
from datetime import datetime, time



@login_required
def nueva_venta(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 1. Obtener datos básicos
                cliente_id = request.POST.get('cliente')
                metodo_pago = request.POST.get('metodo_pago')
                # El carrito viene como un string JSON desde el frontend
                carrito_json = request.POST.get('carrito_data') 
                carrito = json.loads(carrito_json)

                if not carrito:
                    messages.error(request, "El carrito está vacío.")
                    return redirect('nueva_venta')

                # 2. Crear la Cabecera de la Venta
                venta = Venta.objects.create(
                    cliente_id=cliente_id if cliente_id else None,
                    metodo_pago=metodo_pago,
                    total=0 # Lo calculamos abajo
                )

                total_acumulado = 0

                # 3. Procesar cada ítem del carrito
                for item in carrito:
                    producto = Producto.objects.get(id=item['id'])
                    cantidad = int(item['cantidad'])
                    precio = float(item['precio']) # Usamos el precio del momento
                    
                    subtotal = cantidad * precio
                    total_acumulado += subtotal

                    DetalleVenta.objects.create(
                        venta=venta,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=precio,
                        subtotal=subtotal
                    )

                # 4. Actualizar total final
                venta.total = total_acumulado
                venta.save()
                
                messages.success(request, f"Venta #{venta.id} registrada correctamente.")
                return redirect('detalle_venta', venta_id=venta.id)

        except Exception as e:
            messages.error(request, f"Error al procesar la venta: {str(e)}")
            return redirect('nueva_venta')

    # --- GET: Mostrar pantalla ---
    productos = Producto.objects.all().order_by('descripcion')
    clientes = Cliente.objects.all().order_by('apellido')
    
    return render(request, 'sales/nueva_venta.html', {
        'productos': productos,
        'clientes': clientes
    })

@login_required
def lista_ventas(request):
    # Traemos todas las ventas, la más reciente primero
    ventas = Venta.objects.select_related('cliente').all().order_by('-fecha')
    return render(request, 'sales/lista_ventas.html', {'ventas': ventas})

@login_required
def detalle_venta(request, venta_id):
    # Esta es la vista del Ticket
    venta = get_object_or_404(Venta, pk=venta_id)
    return render(request, 'sales/detalle_venta.html', {'venta': venta})

@login_required
def reporte_caja(request):
    # Obtenemos la fecha de hoy
    hoy = timezone.now().date()
    
    # Filtramos ventas de hoy
    ventas_hoy = Venta.objects.filter(fecha__date=hoy)
    
    # Calculamos totales por método de pago
    resumen = ventas_hoy.values('metodo_pago').annotate(total_acumulado=Sum('total'))
    
    # Calculamos el gran total del día
    total_general = ventas_hoy.aggregate(Sum('total'))['total__sum'] or 0
    
    return render(request, 'sales/reporte_caja.html', {
        'fecha': hoy,
        'resumen': resumen,
        'total_general': total_general,
        'cantidad_ventas': ventas_hoy.count(),
        'movimientos': ventas_hoy.order_by('-fecha')
    })

@login_required
def reporte_caja(request):
    # 1. Obtener parámetros del filtro (GET)
    fecha_str = request.GET.get('fecha')
    turno = request.GET.get('turno', 'todo') # Por defecto: todo el día

    # 2. Determinar la fecha a consultar
    if fecha_str:
        try:
            fecha_filtro = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha_filtro = timezone.now().date()
    else:
        fecha_filtro = timezone.now().date()
    
    # 3. Filtrar por Fecha Base
    ventas = Venta.objects.filter(fecha__date=fecha_filtro)
    
    # 4. Filtrar por Turno (Hora)
    if turno == 'manana':
        # Ventas antes de las 14:00
        ventas = ventas.filter(fecha__time__lt=time(14, 0))
    elif turno == 'tarde':
        # Ventas desde las 14:00 en adelante
        ventas = ventas.filter(fecha__time__gte=time(14, 0))
    
    # 5. Calcular Totales (Sobre el queryset ya filtrado)
    total_general = ventas.aggregate(Sum('total'))['total__sum'] or 0
    
    desglose_pagos = ventas.values('metodo_pago').annotate(
        cantidad=Count('id'),
        total=Sum('total')
    ).order_by('metodo_pago')
    
    return render(request, 'sales/reporte_caja.html', {
        'ventas': ventas.order_by('-fecha'),
        'total_general': total_general,
        'desglose': desglose_pagos,
        # Pasamos los filtros de vuelta al template para que no se borren del formulario
        'fecha_seleccionada': fecha_filtro, 
        'turno_seleccionado': turno
    })