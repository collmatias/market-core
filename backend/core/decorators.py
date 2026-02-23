from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def clinico_requerido(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Solo pasa si su profesión es VETERINARIO (o si es superuser de consola)
        es_clinico = request.user.is_superuser or (
            hasattr(request.user, 'profile') and request.user.profile.es_clinico
        )
        if es_clinico:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Acceso restringido: Solo el personal Veterinario puede modificar historiales de salud.")
            return redirect('lista_pacientes') 
    return _wrapped_view

def admin_requerido(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Solo pasa si tiene el TAG es_admin = True
        es_admin = request.user.is_superuser or (
            hasattr(request.user, 'profile') and request.user.profile.es_admin
        )
        if es_admin:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Acceso restringido: Solo Administradores pueden realizar esta acción.")
            return redirect('home')
    return _wrapped_view