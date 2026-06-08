from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0002_report'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='work_end_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
