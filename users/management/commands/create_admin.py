from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create or update the JobLink admin account'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            default='admin@joblink.test',
        )
        parser.add_argument(
            '--password',
            default='Admin1234!',
        )

    def handle(self, *args, **options):
        email = options['email'].strip().lower()
        password = options['password']

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'full_name': 'JobLink Admin',
                'phone_number': '0780000000',
                'role': 'client',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'is_email_verified': True,
            },
        )
        if not created:
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.is_email_verified = True

        user.set_password(password)
        if not user.profile_photo:
            user.profile_photo = (
                'https://res.cloudinary.com/demo/image/upload/'
                'w_400,h_400,c_fill,g_face/sample.jpg'
            )
        user.save()

        action = 'Created' if created else 'Updated'
        self.stdout.write(
            self.style.SUCCESS(
                f'{action} admin: {email} / {password}',
            ),
        )
