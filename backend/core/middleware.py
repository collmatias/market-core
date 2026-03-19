from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from django.utils import translation
from django.contrib import messages
from django.utils.translation import gettext as _
from .license import check_license, get_hardware_id
from .models import Company
from django.contrib.auth.models import User
import os


class LicenseCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        setup_url = reverse('setup_wizard')

        exempt_prefixes = ['/static/', '/media/', '/download/', '/register/', '/verify-email/', '/password-reset/', setup_url]
        for prefix in exempt_prefixes:
            if request.path.startswith(prefix):
                return self.get_response(request)

        if not User.objects.exists():
            return redirect('setup_wizard')

        allowed_paths = [
            reverse('activation'),
            reverse('login'),
            '/admin/',
            reverse('company_settings'),
        ]
        for path in allowed_paths:
            if request.path.startswith(path):
                return self.get_response(request)

        if not os.environ.get('VETCORE_MODE'):
            deployment = getattr(settings, 'DEPLOYMENT_MODE', 'DESKTOP')
            if deployment == 'DESKTOP':
                is_valid, hw_id = check_license()
                if not is_valid:
                    return redirect('activation')

        # Hardware mismatch detection (warning banner, non-blocking)
        if request.user.is_authenticated:
            try:
                company = request.user.profile.company
                if company.is_setup_complete and company.hardware_id:
                    current_hw = get_hardware_id()
                    if company.hardware_id != current_hw:
                        messages.warning(
                            request,
                            _('Hardware change detected. Your system hardware ID does not match '
                              'the registered one. Contact support to transfer your license.')
                        )
            except Exception:
                pass

        return self.get_response(request)


class CompanyLanguageMiddleware:
    """Sets the active language based on the company's language preference."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                lang = request.user.profile.company.language
                translation.activate(lang)
                request.LANGUAGE_CODE = lang
            except Exception:
                pass
        response = self.get_response(request)
        return response


class SaaSReadOnlyMiddleware:
    """Block write operations for VET accounts on SaaS (cloud data is read-only).

    Marketplace and order paths remain writable (orders live in the cloud).
    Auth, profile, and system paths remain writable.
    """

    # Prefixes where writes are ALWAYS allowed (even for readonly VET accounts)
    WRITABLE_PREFIXES = (
        '/marketplace/',
        '/login/', '/logout/',
        '/register/', '/verify-email/', '/password-reset/',
        '/profile/', '/switch-user/',
        '/settings/', '/admin/', '/activate/', '/setup/',
        '/catalog/',
        '/platform/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return self.get_response(request)

        if not request.user.is_authenticated:
            return self.get_response(request)

        try:
            deployment = getattr(settings, 'DEPLOYMENT_MODE', 'DESKTOP')
            if deployment != 'SAAS':
                return self.get_response(request)

            acct = request.user.profile.company.account_type
            if acct != 'VET':
                return self.get_response(request)
        except Exception:
            return self.get_response(request)

        # VET on SaaS — check if path is writable
        for prefix in self.WRITABLE_PREFIXES:
            if request.path.startswith(prefix):
                return self.get_response(request)

        # Block the write
        messages.warning(
            request,
            _('This action is not available in cloud mode. '
              'Clinical, inventory, and sales modifications can only be made from your local system.')
        )
        return redirect(request.META.get('HTTP_REFERER', '/'))
