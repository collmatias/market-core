from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static

from core.views import ClientViewSet, PatientViewSet
from inventory.views import ProductViewSet, StockMovementViewSet

router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'movements', StockMovementViewSet, basename='movement')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),

    path('', include('core.urls')),
    path('', include('clinical.urls')),
    path('', include('inventory.urls')),
    path('', include('sales.urls')),
    path('platform/', include('platform_admin.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
