def currency_context(request):
    if request.user.is_authenticated:
        try:
            return {'currency_code': request.user.profile.company.currency}
        except Exception:
            pass
    return {'currency_code': 'ARS'}


def server_context(request):
    from django.conf import settings as django_settings
    host = request.get_host().split(':')[0].lower()
    return {
        'is_localhost': host in ('localhost', '127.0.0.1', '::1'),
        'deployment_mode': getattr(django_settings, 'DEPLOYMENT_MODE', 'DESKTOP'),
    }


def account_context(request):
    """Expose account_type, helper flags, and SaaS read-only state to all templates."""
    from django.conf import settings as django_settings
    if request.user.is_authenticated:
        try:
            acct = request.user.profile.company.account_type
            is_saas = getattr(django_settings, 'DEPLOYMENT_MODE', 'DESKTOP') == 'SAAS'
            return {
                'account_type': acct,
                'is_vet': acct == 'VET',
                'is_supplier': acct == 'SUPPLIER',
                'is_readonly': is_saas and acct == 'VET',
            }
        except Exception:
            pass
    return {
        'account_type': 'VET',
        'is_vet': True,
        'is_supplier': False,
        'is_readonly': False,
    }
