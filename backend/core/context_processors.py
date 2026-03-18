def currency_context(request):
    if request.user.is_authenticated:
        try:
            return {'currency_code': request.user.profile.company.currency}
        except Exception:
            pass
    return {'currency_code': 'ARS'}


def server_context(request):
    host = request.get_host().split(':')[0].lower()
    return {'is_localhost': host in ('localhost', '127.0.0.1', '::1')}
