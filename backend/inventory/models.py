from django.db import models
from django.contrib.auth.models import User
from core.models import Company, TenantManager


class Product(models.Model):
    TYPE_CHOICES = [
        ('PRODUCT', 'Physical Product'),
        ('SERVICE', 'Service'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True)
    barcode = models.CharField(max_length=50, unique=True, blank=True, null=True)
    description = models.CharField(max_length=200)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='PRODUCT')
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_stock = models.IntegerField(default=0)
    minimum_stock = models.IntegerField(default=5)
    objects = TenantManager()

    @property
    def needs_restock(self):
        if self.type == 'SERVICE':
            return False
        return self.current_stock <= self.minimum_stock

    def __str__(self):
        return self.description


class StockMovement(models.Model):
    TYPES = [
        ('IN', 'Purchase/Incoming'),
        ('OUT', 'Sale/Internal Use'),
        ('ADJUST', 'Adjustment'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=10, choices=TYPES)
    quantity = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    note = models.CharField(max_length=200, blank=True, default='')

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.type in ['OUT', 'ADJUST'] and self.quantity > 0:
                self.quantity = self.quantity * -1
            self.product.current_stock += self.quantity
            self.product.save()
        super().save(*args, **kwargs)
