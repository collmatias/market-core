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
