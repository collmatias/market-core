from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from .models import Producto, MovimientoStock
from .serializers import ProductoSerializer, MovimientoStockSerializer

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all().order_by('descripcion')
    serializer_class = ProductoSerializer

class MovimientoStockViewSet(viewsets.ModelViewSet):
    queryset = MovimientoStock.objects.all().order_by('-fecha')
    serializer_class = MovimientoStockSerializer