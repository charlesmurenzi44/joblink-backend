from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_user_is_email_verified_emailverification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workerprofile',
            name='skill_category',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
