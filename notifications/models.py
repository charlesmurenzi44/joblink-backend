from django.db import models
from users.models import User


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('job_posted', 'Job Posted Nearby'),
        ('job_accepted', 'Job Accepted'),
        ('job_completed', 'Job Completed'),
        ('new_application', 'New Application'),
        ('application_submitted', 'Application Submitted'),
        ('application_rejected', 'Application Rejected'),
        ('new_message', 'New Message'),
        ('emergency_job', 'Emergency Job Nearby'),
        ('review_received', 'Review Received'),
        ('verification_approved', 'Verification Approved'),
        ('verification_rejected', 'Verification Rejected'),
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    body = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recipient.full_name} - {self.title}"


class FCMToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='fcm_token')
    token = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"FCM Token - {self.user.full_name}"