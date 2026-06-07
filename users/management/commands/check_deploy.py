from django.core.management.base import BaseCommand
from django.conf import settings

from users.email_utils import email_configured
from users.sms_utils import sms_configured


class Command(BaseCommand):
    help = 'Check production deploy readiness (run before Railway deploy)'

    def handle(self, *args, **options):
        ok = True
        self.stdout.write('JobLink deploy checklist\n')

        if settings.DEBUG:
            self.stdout.write(
                self.style.WARNING('DEBUG=True — set DEBUG=False on Railway'),
            )
        else:
            self.stdout.write(self.style.SUCCESS('DEBUG=False'))

        secret = settings.SECRET_KEY
        if 'insecure' in secret or 'change-this' in secret:
            self.stdout.write(
                self.style.ERROR('SECRET_KEY is still the dev default'),
            )
            ok = False
        else:
            self.stdout.write(self.style.SUCCESS('SECRET_KEY looks set'))

        db = settings.DATABASES['default']['ENGINE']
        if 'sqlite' in db:
            self.stdout.write(
                self.style.WARNING(
                    'Using SQLite — add PostgreSQL on Railway and link DATABASE_URL',
                ),
            )
        else:
            self.stdout.write(self.style.SUCCESS(f'Database: {db}'))

        if email_configured():
            self.stdout.write(self.style.SUCCESS('Email: configured'))
        else:
            self.stdout.write(self.style.WARNING('Email: not configured'))

        if sms_configured():
            self.stdout.write(self.style.SUCCESS('SMS: configured'))
        else:
            self.stdout.write(self.style.WARNING('SMS: not configured'))

        cloud = settings.CLOUDINARY_STORAGE.get('API_SECRET')
        if cloud:
            self.stdout.write(self.style.SUCCESS('Cloudinary: configured'))
        else:
            self.stdout.write(self.style.ERROR('Cloudinary: missing API secret'))
            ok = False

        self.stdout.write(f'\nALLOWED_HOSTS: {settings.ALLOWED_HOSTS}')
        self.stdout.write(f'Health check: GET /api/health/')

        if ok:
            self.stdout.write(self.style.SUCCESS('\nReady to deploy.'))
        else:
            self.stdout.write(self.style.ERROR('\nFix errors above before deploy.'))
