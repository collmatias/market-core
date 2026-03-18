from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import SaleItem


@receiver(post_save, sender=SaleItem)
def deduct_stock(sender, instance, created, **kwargs):
    if created:
        product = instance.product
        if product.type == 'PRODUCT':
            product.current_stock -= instance.quantity
            product.save()


@receiver(post_delete, sender=SaleItem)
def restore_stock(sender, instance, **kwargs):
    product = instance.product
    if product.type == 'PRODUCT':
        product.current_stock += instance.quantity
        product.save()
