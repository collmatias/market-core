from rest_framework import serializers
from .models import Producto, MovimientoStock

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'

class MovimientoStockSerializer(serializers.ModelSerializer):
    nombre_producto = serializers.ReadOnlyField(source='producto.descripcion')
    
    class Meta:
        model = MovimientoStock
        fields = '__all__'