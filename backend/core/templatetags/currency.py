from django import template
from django.utils.safestring import mark_safe

register = template.Library()

CURRENCY_CONFIG = {
    'ARS': ('$', 2, ',', '.'),
    'USD': ('US$', 2, '.', ','),
    'EUR': ('€', 2, ',', '.'),
    'BRL': ('R$', 2, ',', '.'),
    'CLP': ('CLP$', 0, '', '.'),
    'MXN': ('MX$', 2, '.', ','),
    'UYU': ('$U', 2, ',', '.'),
    'PYG': ('₲', 0, '', '.'),
    'COP': ('COL$', 0, '', '.'),
    'PEN': ('S/', 2, '.', ','),
    'BOB': ('Bs', 2, ',', '.'),
}


def _get_currency(context):
    if 'currency_code' in context:
        return context['currency_code']
    request = context.get('request')
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        try:
            return request.user.profile.company.currency
        except Exception:
            pass
    return 'ARS'


def _format_currency(value, currency_code):
    try:
        value = float(value)
    except (ValueError, TypeError):
        return str(value)

    config = CURRENCY_CONFIG.get(currency_code, CURRENCY_CONFIG['ARS'])
    symbol, decimals, dec_sep, thou_sep = config

    if decimals > 0:
        int_part = int(abs(value))
        dec_part = round(abs(value) - int_part, decimals)
        dec_str = f"{dec_part:.{decimals}f}"[2:]
    else:
        int_part = round(abs(value))
        dec_str = ''

    int_str = ''
    s = str(int_part)
    for i, digit in enumerate(reversed(s)):
        if i > 0 and i % 3 == 0 and thou_sep:
            int_str = thou_sep + int_str
        int_str = digit + int_str

    if dec_str:
        number = f"{int_str}{dec_sep}{dec_str}"
    else:
        number = int_str

    sign = '-' if value < 0 else ''
    return f"{sign}{symbol}{number}"


@register.simple_tag(takes_context=True)
def currency(context, value):
    """Format a value with the company's currency symbol and format.
    Usage: {% currency price %}
    """
    code = _get_currency(context)
    return _format_currency(value, code)


@register.simple_tag(takes_context=True)
def currency_symbol(context):
    """Return just the currency symbol.
    Usage: {% currency_symbol %}
    """
    code = _get_currency(context)
    config = CURRENCY_CONFIG.get(code, CURRENCY_CONFIG['ARS'])
    return config[0]


@register.simple_tag(takes_context=True)
def currency_config_js(context):
    """Return currency config as a JS object string.
    Usage: {% currency_config_js %}
    """
    code = _get_currency(context)
    config = CURRENCY_CONFIG.get(code, CURRENCY_CONFIG['ARS'])
    symbol, decimals, dec_sep, thou_sep = config
    return mark_safe(
        f'{{"symbol":"{symbol}","decimals":{decimals},'
        f'"dec_sep":"{dec_sep}","thou_sep":"{thou_sep}"}}'
    )
