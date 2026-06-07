from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from jobs.models import Job, JobCategory, JobApplication

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed demo users, categories, and sample jobs'

    def handle(self, *args, **options):
        from django.core.management import call_command

        call_command('seed_categories')

        demos = [
            {
                'email': 'client@joblink.test',
                'full_name': 'Demo Client',
                'phone': '0781111111',
                'role': 'client',
                'password': 'Demo1234!',
            },
            {
                'email': 'worker@joblink.test',
                'full_name': 'Demo Worker',
                'phone': '0782222222',
                'role': 'worker',
                'password': 'Demo1234!',
            },
        ]

        for d in demos:
            user, created = User.objects.get_or_create(
                email=d['email'],
                defaults={
                    'full_name': d['full_name'],
                    'phone_number': d['phone'],
                    'role': d['role'],
                    'is_active': True,
                    'is_email_verified': True,
                    'latitude': -1.9441,
                    'longitude': 30.0619,
                    'district': 'Gasabo',
                    'profile_photo': (
                        'https://res.cloudinary.com/demo/image/upload/'
                        'w_400,h_400,c_fill,g_face/sample.jpg'
                    ),
                },
            )
            user.set_password(d['password'])
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"{'Created' if created else 'Updated'} {d['role']}: "
                    f"{d['email']} / {d['password']}",
                ),
            )

            if d['role'] == 'worker':
                from users.models import WorkerProfile
                wp, _ = WorkerProfile.objects.get_or_create(user=user)
                wp.skill_category = wp.skill_category or 'Electrician'
                wp.daily_rate = wp.daily_rate or 15000
                wp.is_available = True
                wp.verification_status = 'verified'
                wp.save()

        call_command('create_admin')

        client = User.objects.get(email='client@joblink.test')
        worker = User.objects.get(email='worker@joblink.test')
        cat = JobCategory.objects.first()

        job, created = Job.objects.get_or_create(
            title='Fix kitchen wiring',
            client=client,
            defaults={
                'description': 'Need an electrician to fix kitchen outlets.',
                'status': 'posted',
                'category': cat,
                'latitude': -1.9441,
                'longitude': 30.0619,
                'district': 'Gasabo',
                'budget': 25000,
                'payment_method': 'momo',
                'scheduled_date': timezone.now().date(),
                'work_end_date': timezone.now().date() + timedelta(days=1),
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Sample job created: {job.title}'))
        else:
            self.stdout.write(f'Sample job exists: {job.title}')

        wp = worker.worker_profile
        if not JobApplication.objects.filter(job=job, worker=wp).exists():
            JobApplication.objects.create(
                job=job,
                worker=wp,
                cover_note='I can come today.',
                proposed_rate=22000,
            )
            self.stdout.write(self.style.SUCCESS('Sample application created'))

        self.stdout.write(self.style.SUCCESS('Demo seed complete.'))
