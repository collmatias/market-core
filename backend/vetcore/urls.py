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
from django.contrib.auth import views as auth_views


# Importamos las vistas (API)
from core.views import ClienteViewSet, PacienteViewSet, HistoriaClinicaViewSet

# Core Views
from core.views import (
    home,
    lista_clientes, crear_cliente, 
    lista_pacientes, crear_paciente
)
# Inventory Views
from inventory.views import ProductoViewSet, MovimientoStockViewSet
from inventory.views import lista_productos, crear_producto, registrar_movimiento

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

    # --- HOME Y AUTH ---
    path('', home, name='home'), # La raíz del sitio
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Rutas del Frontend (Templates)
    path('clientes/', lista_clientes, name='lista_clientes'),
    path('clientes/nuevo/', crear_cliente, name='crear_cliente'),

    # Rutas Pacientes
    path('pacientes/', lista_pacientes, name='lista_pacientes'),
    path('pacientes/nuevo/', crear_paciente, name='crear_paciente'),

    # Rutas de Inventario
    path('productos/', lista_productos, name='lista_productos'),
    path('productos/nuevo/', crear_producto, name='crear_producto'),
    path('stock/movimiento/', registrar_movimiento, name='registrar_movimiento'),
]
