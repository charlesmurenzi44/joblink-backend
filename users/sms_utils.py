import logging

import requests
from django.conf import settings

from .phone_utils import normalize_phone

logger = logging.getLogger(__name__)


class SmsDeliveryError(Exception):
    pass


def sms_configured() -> bool:
    provider = (getattr(settings, 'SMS_PROVIDER', '') or '').lower()
    if provider == 'twilio':
        return bool(
            settings.TWILIO_ACCOUNT_SID
            and settings.TWILIO_AUTH_TOKEN
            and settings.TWILIO_FROM_NUMBER
        )
    if provider == 'africastalking':
        return bool(
            settings.AFRICASTALKING_USERNAME
            and settings.AFRICASTALKING_API_KEY
        )
    return False


def _send_via_africastalking(phone: str, message: str) -> None:
    username = settings.AFRICASTALKING_USERNAME
    api_key = settings.AFRICASTALKING_API_KEY
    sender = settings.AFRICASTALKING_SENDER or None
    sandbox = getattr(settings, 'AFRICASTALKING_SANDBOX', True)

    base = (
        'https://api.sandbox.africastalking.com'
        if sandbox
        else 'https://api.africastalking.com'
    )
    url = f'{base}/version1/messaging'

    data = {
        'username': username,
        'to': phone,
        'message': message,
    }
    if sender:
        data['from'] = sender

    response = requests.post(
        url,
        data=data,
        headers={
            'apiKey': api_key,
            'Accept': 'application/json',
        },
        timeout=20,
    )

    if response.status_code >= 400:
        raise SmsDeliveryError(
            f'Africa\'s Talking HTTP {response.status_code}: {response.text[:200]}',
        )

    try:
        payload = response.json()
    except ValueError:
        logger.info('Africa\'s Talking raw response: %s', response.text[:300])
        return

    recipients = (
        payload.get('SMSMessageData', {}).get('Recipients')
        or payload.get('recipients')
        or []
    )
    if recipients:
        status = str(recipients[0].get('status', '')).lower()
        if status not in ('success', 'sent', 'submitted', 'queued'):
            raise SmsDeliveryError(
                f'SMS rejected: {recipients[0].get("statusCode")} '
                f'{recipients[0].get("status")}',
            )


def _send_via_twilio(phone: str, message: str) -> None:
    sid = settings.TWILIO_ACCOUNT_SID
    token = settings.TWILIO_AUTH_TOKEN
    from_number = settings.TWILIO_FROM_NUMBER

    url = f'https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json'
    response = requests.post(
        url,
        data={'To': phone, 'From': from_number, 'Body': message},
        auth=(sid, token),
        timeout=20,
    )
    if response.status_code >= 400:
        raise SmsDeliveryError(
            f'Twilio HTTP {response.status_code}: {response.text[:200]}',
        )


def send_sms(phone: str, message: str) -> bool:
    """
    Send SMS using configured provider.
    Returns True when sent via provider, False when logged to console (dev).
    Raises SmsDeliveryError when provider is configured but delivery fails.
    """
    normalized = normalize_phone(phone)
    if not normalized:
        raise SmsDeliveryError('Invalid phone number')

    if not sms_configured():
        logger.info('SMS (dev console): %s -> %s', normalized, message)
        print(f'\n{"=" * 40}\nSMS to {normalized}: {message}\n{"=" * 40}\n')
        return False

    provider = (getattr(settings, 'SMS_PROVIDER', '') or '').lower()

    if provider == 'africastalking':
        _send_via_africastalking(normalized, message)
        logger.info('SMS sent via Africa\'s Talking to %s', normalized)
        return True

    if provider == 'twilio':
        _send_via_twilio(normalized, message)
        logger.info('SMS sent via Twilio to %s', normalized)
        return True

    logger.warning('Unknown SMS_PROVIDER=%s', provider)
    print(f'\n{"=" * 40}\nSMS to {normalized}: {message}\n{"=" * 40}\n')
    return False
