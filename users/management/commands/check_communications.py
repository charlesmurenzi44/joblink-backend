from django.core.management.base import BaseCommand

from users.email_utils import email_configured
from users.sms_utils import sms_configured


class Command(BaseCommand):
    help = 'Show email and SMS configuration status'

    def handle(self, *args, **options):
        self.stdout.write('JobLink communications status\n')

        if email_configured():
            self.stdout.write(self.style.SUCCESS('Email: configured (SMTP)'))
            self.stdout.write(
                '  Test: python manage.py check_email --to=you@example.com',
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Email: NOT configured — codes print to Django console',
                ),
            )
            self.stdout.write(
                '  Set EMAIL_HOST_USER + EMAIL_HOST_PASSWORD in .env (Gmail app password)',
            )

        if sms_configured():
            self.stdout.write(self.style.SUCCESS('SMS: configured'))
            self.stdout.write(
                '  Test: python manage.py check_sms --phone=+250781234567',
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    'SMS: NOT configured — OTP prints to Django console',
                ),
            )
            self.stdout.write(
                '  Set SMS_PROVIDER=africastalking (or twilio) + credentials in .env',
            )
