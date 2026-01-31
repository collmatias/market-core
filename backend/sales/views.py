import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from .models import Venta, DetalleVenta
from inventory.models import Producto
from core.models import Cliente
from django.shortcuts import render, redirect, get_object_or_404 

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
                return redirect('detalle_venta', venta_id=venta.id) # <--- IMPORTANTE: Usar detalle_venta

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

# --- VISTAS NUEVAS ---

def lista_ventas(request):
    # Traemos todas las ventas, la más reciente primero
    ventas = Venta.objects.select_related('cliente').all().order_by('-fecha')
    return render(request, 'sales/lista_ventas.html', {'ventas': ventas})

def detalle_venta(request, venta_id):
    # Esta es la vista del Ticket
    venta = get_object_or_404(Venta, pk=venta_id)
    return render(request, 'sales/detalle_venta.html', {'venta': venta})

    