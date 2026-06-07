from django.core.management.base import BaseCommand
from django.conf import settings

from users.email_utils import email_configured, send_verification_email
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Send a test verification email'

    def add_arguments(self, parser):
        parser.add_argument('--to', required=True, help='Recipient email')

    def handle(self, *args, **options):
        if not email_configured():
            self.stderr.write(
                self.style.ERROR(
                    'Email not configured. Set EMAIL_HOST_USER and '
                    'EMAIL_HOST_PASSWORD in .env (Gmail app password).',
                ),
            )
            return

        to = options['to'].strip()
        user, _ = User.objects.get_or_create(
            email=to,
            defaults={
                'full_name': 'JobLink Test',
                'phone_number': '0780000001',
                'role': 'client',
            },
        )

        sent, err = send_verification_email(user, '123456', 'test-token')
        if sent:
            self.stdout.write(
                self.style.SUCCESS(f'Test email sent to {to} via {settings.EMAIL_HOST}'),
            )
        else:
            self.stderr.write(self.style.ERROR(f'Failed: {err}'))
