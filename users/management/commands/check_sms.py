from django.core.management.base import BaseCommand

from users.sms_utils import SmsDeliveryError, send_sms, sms_configured


class Command(BaseCommand):
    help = 'Send a test SMS OTP'

    def add_arguments(self, parser):
        parser.add_argument('--phone', required=True, help='Phone e.g. +250781234567')

    def handle(self, *args, **options):
        phone = options['phone'].strip()
        if not sms_configured():
            self.stderr.write(
                self.style.WARNING(
                    'SMS provider not configured. Set SMS_PROVIDER and credentials '
                    'in .env. Running in console/dev mode.',
                ),
            )

        try:
            sent = send_sms(phone, 'JobLink test SMS — your setup works.')
        except SmsDeliveryError as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            return

        if sent:
            self.stdout.write(self.style.SUCCESS(f'SMS sent to {phone}'))
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'SMS logged to console for {phone} (configure SMS_PROVIDER for real SMS)',
                ),
            )
