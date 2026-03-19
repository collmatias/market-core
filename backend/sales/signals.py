from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import SaleItem
from inventory.models import StockMovement


@receiver(post_save, sender=SaleItem)
def deduct_stock(sender, instance, created, **kwargs):
    if created:
        product = instance.product
        if product.type == 'PRODUCT':
            StockMovement.objects.create(
                product=product,
                type='OUT',
                quantity=instance.quantity,
                note=f'Venta #{instance.sale_id}',
            )


@receiver(post_delete, sender=SaleItem)
def restore_stock(sender, instance, **kwargs):
    product = instance.product
    if product.type == 'PRODUCT':
        StockMovement.objects.create(
            product=product,
            type='IN',
            quantity=instance.quantity,
            note=f'Anulación venta #{instance.sale_id}',
        )
