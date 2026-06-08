from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0004_review_both_parties'),
        ('users', '0004_user_employer_ratings'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='payment_status',
            field=models.CharField(
                choices=[
                    ('unpaid', 'Unpaid'),
                    ('held', 'Held in Escrow'),
                    ('released', 'Released to Worker'),
                    ('disputed', 'Disputed'),
                ],
                default='unpaid',
                max_length=10,
            ),
        ),
        migrations.CreateModel(
            name='JobActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[
                    ('posted', 'Job Posted'),
                    ('application_received', 'Application Received'),
                    ('worker_hired', 'Worker Hired'),
                    ('started', 'Work Started'),
                    ('completion_submitted', 'Completion Proof Submitted'),
                    ('completed', 'Job Completed'),
                    ('payment_held', 'Payment Held'),
                    ('payment_released', 'Payment Released'),
                    ('dispute_opened', 'Dispute Opened'),
                    ('reviewed', 'Review Submitted'),
                    ('cancelled', 'Job Cancelled'),
                ], max_length=30)),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.user')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities', to='jobs.job')),
            ],
            options={
                'verbose_name_plural': 'Job activities',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='JobCompletionProof',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completion_note', models.TextField()),
                ('photo_urls', models.JSONField(blank=True, default=list)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('job', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='completion_proof', to='jobs.job')),
                ('worker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.workerprofile')),
            ],
        ),
    ]
