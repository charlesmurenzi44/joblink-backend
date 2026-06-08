from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0003_job_work_end_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='review',
            name='job',
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                related_name='reviews',
                to='jobs.job',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='review',
            unique_together={('job', 'reviewer')},
        ),
    ]
