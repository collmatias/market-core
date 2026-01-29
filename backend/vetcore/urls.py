"""
URL configuration for vetcore project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Importamos las vistas
from core.views import ClienteViewSet, PacienteViewSet, HistoriaClinicaViewSet
from inventory.views import ProductoViewSet, MovimientoStockViewSet

# Configuramos el Router
router = DefaultRouter()
# Rutas de Core
router.register(r'clientes', ClienteViewSet)
router.register(r'pacientes', PacienteViewSet)
router.register(r'historias', HistoriaClinicaViewSet)
# Rutas de Inventory
router.register(r'productos', ProductoViewSet)
router.register(r'movimientos', MovimientoStockViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)), # Todas las rutas API colgarán de /api/
]