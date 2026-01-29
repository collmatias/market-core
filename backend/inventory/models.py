from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Producto(models.Model):
    codigo_barras = models.CharField(max_length=50, unique=True, blank=True, null=True)
    descripcion = models.CharField(max_length=200)
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad_actual = models.IntegerField(default=0)
    cantidad_minima = models.IntegerField(default=5)
    
    @property
    def necesita_reposicion(self):
        return self.cantidad_actual <= self.cantidad_minima

    def __str__(self):
        return f"{self.descripcion}"

class MovimientoStock(models.Model):
    TIPO = [('ENTRADA', 'Compra/Ingreso'), ('SALIDA', 'Venta/Uso Interno'), ('AJUSTE', 'Corrección')]
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=10, choices=TIPO)
    cantidad = models.IntegerField()
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        # Lógica simple de actualización de stock
        if not self.pk: 
            if self.tipo in ['SALIDA', 'AJUSTE'] and self.cantidad > 0:
                 self.cantidad = self.cantidad * -1
            self.producto.cantidad_actual += self.cantidad
            self.producto.save()
        super().save(*args, **kwargs)