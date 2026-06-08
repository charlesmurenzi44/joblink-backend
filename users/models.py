from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import uuid

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('client', 'Client'),
        ('worker', 'Worker'),
    )

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15, unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    profile_photo = models.TextField(blank=True, null=True)  # stores Cloudinary URL
    is_email_verified = models.BooleanField(default=False)

    # Location
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    district = models.CharField(max_length=100, blank=True)  # e.g Gasabo, Rulindo
    sector = models.CharField(max_length=100, blank=True)    # e.g Kimironko

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    # Ratings received as an employer (from workers)
    employer_average_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.00)
    employer_total_reviews = models.PositiveIntegerField(default=0)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'phone_number', 'role']

    def __str__(self):
        return f"{self.full_name} ({self.role})"


class WorkerProfile(models.Model):
    VERIFICATION_STATUS = (
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='worker_profile')
    bio = models.TextField(blank=True)
    skill_category = models.CharField(
        max_length=100, blank=True, default='',
    )  # e.g Electrician, Plumber — set during onboarding
    experience_years = models.PositiveIntegerField(default=0)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Verification
    verification_status = models.CharField(max_length=10, choices=VERIFICATION_STATUS, default='pending')
    id_document = models.ImageField(upload_to='verifications/', blank=True, null=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    # Availability
    is_available = models.BooleanField(default=True)
    available_days = models.JSONField(default=list)  # e.g ["Monday", "Tuesday"]

    # Ratings
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.PositiveIntegerField(default=0)
    total_jobs_done = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.skill_category}"


class WorkerPortfolio(models.Model):
    worker = models.ForeignKey(
        WorkerProfile, on_delete=models.CASCADE,
        related_name='portfolio')
    image = models.TextField()  # stores Cloudinary URL
    description = models.CharField(
        max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Portfolio of {self.worker.user.full_name}"

class SavedWorker(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_workers')
    worker = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('client', 'worker')

    def __str__(self):
        return f"{self.client.full_name} saved {self.worker.user.full_name}"

class OTPVerification(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='otp')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"OTP for {self.user.full_name}"


class VerificationRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    worker = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='verification_request')
    id_photo = models.TextField()       # Cloudinary URL
    selfie_photo = models.TextField()   # Cloudinary URL
    id_number = models.CharField(max_length=50, blank=True)
    phone_verified = models.BooleanField(default=False)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending')
    admin_note = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Verification: {self.worker.full_name} - {self.status}"
     

class EmailVerification(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='email_verification')
    code = models.CharField(max_length=6)
    token = models.UUIDField(default=uuid.uuid4)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"EmailVerification for {self.user.email}"


class PasswordReset(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='password_resets')
    code = models.CharField(max_length=6)
    token = models.UUIDField(default=uuid.uuid4)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'PasswordReset for {self.user.email}'