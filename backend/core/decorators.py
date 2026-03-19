from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from functools import wraps


def clinical_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        is_clinical = request.user.is_superuser or (
            hasattr(request.user, 'profile') and request.user.profile.is_clinical
        )
        if is_clinical:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, _("Access restricted: Only veterinary staff can modify health records."))
            return redirect('patient_list')
    return _wrapped_view


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        is_admin = request.user.is_superuser or (
            hasattr(request.user, 'profile') and request.user.profile.is_admin
        )
        if is_admin:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, _("Access restricted: Only administrators can perform this action."))
            return redirect('home')
    return _wrapped_view


def _is_localhost(request):
    """Check if the request originates from the server machine itself."""
    host = request.get_host().split(':')[0].lower()
    return host in ('localhost', '127.0.0.1', '::1')


def localhost_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not _is_localhost(request):
            messages.error(request, _("This operation can only be performed from the server machine."))
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def owner_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        is_owner = request.user.is_superuser or (
            hasattr(request.user, 'profile') and request.user.profile.is_owner
        )
        if is_owner:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, _("Access restricted: Owner permission required."))
            return redirect('home')
    return _wrapped_view
