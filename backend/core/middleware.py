from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from .license import check_license
from .models import Empresa
from django.contrib.auth.models import User

class LicenseCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        setup_url = reverse('setup_wizard') # <--- Nueva ruta

        # 1. EXCEPCIONES: Rutas que siempre pasan (Static, Admin, Setup)
        if request.path.startswith('/static/') or request.path.startswith('/media/') or request.path == setup_url:
             return self.get_response(request)

        # 2. DETECTOR DE INSTALACIÓN LIMPIA
        # Si no hay usuarios en la DB, redirigir al Wizard.
        if not User.objects.exists():
            return redirect('setup_wizard')

        # 1. Rutas permitidas siempre (Login, Static, Admin, Activación)
        allowed_prefixes = [
            reverse('activacion'),
            reverse('login'), # Importante: dejar entrar al login
            '/admin/',
            '/static/',
            '/media/',
            # IMPORTANTE: Permitir la ruta de configuración para no crear un bucle infinito
            reverse('configuracion_empresa'), 
        ]

        for path in allowed_prefixes:
            if request.path.startswith(path):
                return self.get_response(request)

        # 2. VALIDACIÓN DE LICENCIA (Tu código existente Desktop/SaaS...)
        # ... (aquí va tu if SaaS / if Desktop check_license) ...
        # (Copia tu lógica anterior aquí)

        # ----------------------------------------------------
        # 3. VALIDACIÓN DE EMPRESA (NUEVO)
        # ----------------------------------------------------
        if request.user.is_authenticated:
            # Si el usuario no tiene perfil o no hay empresas en la DB
            if not Empresa.objects.exists():
                return redirect('configuracion_empresa')
            
            # Opcional: Si es SaaS y el usuario no tiene empresa asignada
            if hasattr(request, 'user') and not hasattr(request.user, 'userprofile'):
                 return redirect('configuracion_empresa')

        return self.get_response(request)