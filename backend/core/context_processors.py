def currency_context(request):
    if request.user.is_authenticated:
        try:
            return {'currency_code': request.user.profile.company.currency}
        except Exception:
            pass
    return {'currency_code': 'ARS'}
