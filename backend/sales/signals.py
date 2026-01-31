from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import DetalleVenta

@receiver(post_save, sender=DetalleVenta)
def descontar_stock(sender, instance, created, **kwargs):
    """
    Se ejecuta automáticamente cuando se guarda un renglón de venta.
    Si es una venta nueva y es PRODUCTO físico, descuenta stock.
    """
    if created:
        producto = instance.producto
        
        # Solo descontamos si es un producto físico
        if producto.tipo == 'PRODUCTO':
            producto.cantidad_actual -= instance.cantidad
            producto.save()

@receiver(post_delete, sender=DetalleVenta)
def devolver_stock(sender, instance, **kwargs):
    """
    Si borramos una venta (anulación), devolvemos el stock.
    """
    producto = instance.producto
    if producto.tipo == 'PRODUCTO':
        producto.cantidad_actual += instance.cantidad
        producto.save()