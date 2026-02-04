from django.shortcuts import redirect
from django.urls import reverse
from .license import check_license

class LicenseCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Definir rutas que SIEMPRE deben estar abiertas
        # (Activación, Admin para emergencias, y Archivos estáticos)
        allowed_prefixes = [
            reverse('activacion'), # Permitir entrar a la pág de activación
            '/admin/',             # Permitir entrar al admin (opcional, recomendado para soporte)
            '/static/',            # Permitir cargar CSS/JS
            '/media/',             # Permitir cargar imágenes
        ]
        
        # Si la ruta actual empieza con algo permitido, dejar pasar
        for path in allowed_prefixes:
            if request.path.startswith(path):
                return self.get_response(request)

        # 2. Verificar si tiene licencia válida
        is_valid, _ = check_license()
        
        if not is_valid:
            # Si no es válida, redirigir forzosamente a activación
            return redirect('activacion')

        # Si todo bien, continuar normal
        return self.get_response(request)