from django.core.management.base import BaseCommand
from jobs.models import JobCategory

CATEGORIES = [
    ('Driver', 'directions_car'),
    ('Electrician', 'electrical_services'),
    ('Plumber', 'plumbing'),
    ('Cleaner', 'cleaning_services'),
    ('Carpenter', 'construction'),
    ('Painter', 'format_paint'),
    ('Gardener', 'yard'),
    ('Mechanic', 'car_repair'),
    ('Mason', 'foundation'),
    ('Tailor', 'checkroom'),
    ('Cook', 'restaurant'),
    ('Security Guard', 'security'),
]


class Command(BaseCommand):
    help = 'Seed default job categories for JobLink'

    def handle(self, *args, **options):
        created = 0
        for name, icon in CATEGORIES:
            _, was_created = JobCategory.objects.get_or_create(
                name=name,
                defaults={'icon': icon},
            )
            if was_created:
                created += 1
        self.stdout.write(
            self.style.SUCCESS(
                f'Done. {created} new categories, '
                f'{JobCategory.objects.count()} total.'
            )
        )
