from django.db import models
from django.utils import timezone
from core.models import Client, Company, TenantManager
from inventory.models import Product


class Sale(models.Model):
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('CARD', 'Debit/Credit Card'),
        ('TRANSFER', 'Bank Transfer'),
        ('QR', 'Digital Wallet (QR)'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True)
    date = models.DateTimeField(default=timezone.now)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, related_name='purchases')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    objects = TenantManager()

    def __str__(self):
        return f"Sale #{self.id} - {self.date.strftime('%d/%m/%Y')}"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity}x {self.product.description}"
