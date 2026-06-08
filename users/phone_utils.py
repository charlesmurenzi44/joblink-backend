import re


def normalize_phone(phone: str, default_country: str = '250') -> str:
    """Normalize to E.164-ish format (+250... for Rwanda)."""
    raw = re.sub(r'[\s\-().]', '', (phone or '').strip())
    if not raw:
        return ''

    if raw.startswith('+'):
        return raw

    if raw.startswith('00'):
        return f'+{raw[2:]}'

    if raw.startswith(default_country):
        return f'+{raw}'

    # Local Rwanda: 078xxxxxxx -> +25078xxxxxxx
    if raw.startswith('0') and len(raw) >= 9:
        return f'+{default_country}{raw[1:]}'

    return f'+{raw}'
