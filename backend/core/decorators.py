from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def clinico_requerido(view_func):
    """
    Decorador que bloquea el acceso a usuarios que NO son ADMIN o VETERINARIO.
    Si es un VENDEDOR, lo rebota con un mensaje de error.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Si es superusuario de consola o tiene perfil clínico (Admin/Vete)
        es_clinico = request.user.is_superuser or (
            hasattr(request.user, 'profile') and request.user.profile.es_clinico
        )
        
        if es_clinico:
            return view_func(request, *args, **kwargs)
        else:
            # Si es Vendedor, lo rebotamos
            messages.error(request, "Acceso restringido: Solo el personal clínico (Veterinarios) puede modificar datos médicos.")
            # Lo mandamos de vuelta a la página anterior o al listado de pacientes
            return redirect('lista_pacientes') 
            
    return _wrapped_view