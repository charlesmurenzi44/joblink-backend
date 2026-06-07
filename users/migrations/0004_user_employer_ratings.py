from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_worker_skill_optional'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='employer_average_rating',
            field=models.DecimalField(
                decimal_places=2, default=0.0, max_digits=3),
        ),
        migrations.AddField(
            model_name='user',
            name='employer_total_reviews',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
