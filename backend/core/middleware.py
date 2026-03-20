from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from django.utils import translation
from .license import check_license
from .models import Company
from django.contrib.auth.models import User
import os


class LicenseCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        setup_url = reverse('setup_wizard')

        exempt_prefixes = ['/static/', '/media/', setup_url]
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

        if not os.environ.get('MARKETCORE_MODE'):
            deployment = getattr(settings, 'DEPLOYMENT_MODE', 'DESKTOP')
            if deployment == 'DESKTOP':
                is_valid, hw_id = check_license()
                if not is_valid:
                    return redirect('activation')

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
