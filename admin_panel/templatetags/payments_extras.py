from django import template
from django.utils.safestring import mark_safe
from admin_panel.models import PaymentOption

register = template.Library()


def _infer_country_from_request(request):
    # Try common headers set by CDNs / reverse proxies
    headers = [
        'HTTP_CF_IPCOUNTRY',
        'HTTP_X_COUNTRY',
        'HTTP_GEOIP_COUNTRY_CODE',
        'GEOIP_COUNTRY_CODE',
        'HTTP_X_APPENGINE_COUNTRY',
    ]
    for h in headers:
        val = request.META.get(h)
        if val:
            return val.strip().upper()
    # Fallback to user profile field if present
    try:
        if hasattr(request, 'user') and request.user.is_authenticated:
            profile = getattr(request.user, 'profile', None)
            if profile is not None and hasattr(profile, 'country'):
                return (profile.country or '').strip().upper()
    except Exception:
        pass
    return None


@register.simple_tag(takes_context=True)
def get_payment_options_for_request(context):
    """Return HTML list of active payment options filtered by the requesting user's country.

    Usage in template:
      {% load payments_extras %}
      {% get_payment_options_for_request as payment_html %}
      {{ payment_html|safe }}
    """
    request = context.get('request')
    if not request:
        options = PaymentOption.objects.filter(active=True)
    else:
        country = _infer_country_from_request(request)
        all_opts = PaymentOption.objects.filter(active=True)
        options = [o for o in all_opts if o.matches_country(country)]

    if not options:
        return mark_safe('<div class="text-sm text-gray-400">No payment options available for your region. Contact support for assistance.</div>')

    html_parts = ['<div class="space-y-4">']
    for opt in options:
        html_parts.append('<div class="p-4 bg-slate-800/20 border border-purple-500/20 rounded-lg">')
        html_parts.append(f'<h4 class="font-semibold text-white">{opt.name} <span class="text-xs text-gray-400">{opt.currency or ""}</span></h4>')
        if opt.instructions:
            # preserve simple newlines
            instr = opt.instructions.replace('\n', '<br/>')
            html_parts.append(f'<p class="text-xs text-gray-300 mt-2">{instr}</p>')
        html_parts.append('</div>')
    html_parts.append('</div>')

    return mark_safe('\n'.join(html_parts))
