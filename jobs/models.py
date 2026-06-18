from django.db import models
from users.models import User, WorkerProfile


class JobCategory(models.Model):
    name = models.CharField(max_length=100)  # e.g Electrician, Plumber
    icon = models.CharField(max_length=100, blank=True)  # icon name for Flutter

    def __str__(self):
        return self.name


class Job(models.Model):
    STATUS_CHOICES = (
        ('posted', 'Posted'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    PAYMENT_CHOICES = (
        ('cash', 'Cash'),
        ('momo', 'Mobile Money'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('unpaid', 'Unpaid'),
        ('held', 'Held in Escrow'),
        ('released', 'Released to Worker'),
        ('disputed', 'Disputed'),
    )

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs_posted')
    worker = models.ForeignKey(WorkerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs_taken')
    category = models.ForeignKey(JobCategory, on_delete=models.SET_NULL, null=True)

    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='posted')

    # Location
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    district = models.CharField(max_length=100)
    sector = models.CharField(max_length=100, blank=True)
    cell = models.CharField(max_length=100, null=True, blank=True)
    village = models.CharField(max_length=100, null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)

    # Payment
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='cash')
    payment_status = models.CharField(
        max_length=10, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    is_negotiable = models.BooleanField(default=True)

    # Emergency
    is_emergency = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    scheduled_date = models.DateField(null=True, blank=True)  # work start
    work_end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.client.full_name}"


class JobApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    worker = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE, related_name='applications')
    proposed_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cover_note = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'worker')

    def __str__(self):
        return f"{self.worker.user.full_name} → {self.job.title}"


class Review(models.Model):
    job = models.ForeignKey(
        Job, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    reviewee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
    rating = models.PositiveSmallIntegerField()  # 1 to 5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'reviewer')

    def __str__(self):
        return f"{self.reviewer.full_name} → {self.reviewee.full_name} ({self.rating}⭐)"


class JobActivity(models.Model):
    EVENT_CHOICES = (
        ('posted', 'Job Posted'),
        ('application_received', 'Application Received'),
        ('worker_hired', 'Worker Hired'),
        ('started', 'Work Started'),
        ('completion_submitted', 'Completion Proof Submitted'),
        ('completed', 'Job Completed'),
        ('payment_held', 'Payment Held'),
        ('payment_released', 'Payment Released'),
        ('dispute_opened', 'Dispute Opened'),
        ('dispute_resolved', 'Dispute Resolved'),
        ('reviewed', 'Review Submitted'),
        ('cancelled', 'Job Cancelled'),
    )

    job = models.ForeignKey(
        Job, on_delete=models.CASCADE, related_name='activities')
    actor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name_plural = 'Job activities'

    def __str__(self):
        return f'{self.job.title} — {self.event_type}'


class JobCompletionProof(models.Model):
    job = models.OneToOneField(
        Job, on_delete=models.CASCADE, related_name='completion_proof')
    worker = models.ForeignKey(
        WorkerProfile, on_delete=models.CASCADE)
    completion_note = models.TextField()
    photo_urls = models.JSONField(default=list, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Proof for {self.job.title}'


class Report(models.Model):
    REASON_CHOICES = (
        ('fraud', 'Fraud'),
        ('no_show', 'No Show'),
        ('bad_behavior', 'Bad Behavior'),
        ('fake_profile', 'Fake Profile'),
        ('poor_work', 'Poor Work Quality'),
        ('other', 'Other'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    )

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received')
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField()
    evidence_urls = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('reporter', 'reported_user', 'job')

    def __str__(self):
        return f"{self.reporter.full_name} reported {self.reported_user.full_name} - {self.reason}"


class MoMoTransaction(models.Model):
    TYPE_CHOICES = (
        ('collection', 'Collection'),
        ('disbursement', 'Disbursement'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    )

    job = models.ForeignKey(
        Job, on_delete=models.CASCADE, related_name='momo_transactions')
    transaction_type = models.CharField(max_length=15, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone = models.CharField(max_length=20)
    reference = models.CharField(max_length=100, unique=True)
    external_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='pending')
    response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.reference} ({self.status})'