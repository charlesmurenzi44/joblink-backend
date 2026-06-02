from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, WorkerProfile, WorkerPortfolio, SavedWorker, OTPVerification, VerificationRequest, OTPVerification, VerificationRequest, EmailVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['full_name', 'email', 'phone_number', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['full_name', 'email', 'phone_number']
    ordering = ['-date_joined']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'phone_number', 'profile_photo')}),
        ('Location', {'fields': ('district', 'sector', 'latitude', 'longitude')}),
        ('Role & Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'phone_number', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'skill_category', 'verification_status', 'is_available', 'average_rating']
    list_filter = ['verification_status', 'is_available', 'skill_category']
    search_fields = ['user__full_name', 'skill_category']
    actions = ['approve_workers', 'reject_workers']

    def approve_workers(self, request, queryset):
        queryset.update(verification_status='verified')
    approve_workers.short_description = 'Approve selected workers'

    def reject_workers(self, request, queryset):
        queryset.update(verification_status='rejected')
    reject_workers.short_description = 'Reject selected workers'


@admin.register(WorkerPortfolio)
class WorkerPortfolioAdmin(admin.ModelAdmin):
    list_display = ['worker', 'description', 'uploaded_at']


@admin.register(SavedWorker)
class SavedWorkerAdmin(admin.ModelAdmin):
    list_display = ['client', 'worker', 'saved_at']


@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ['worker', 'status', 'phone_verified', 'submitted_at', 'reviewed_at']
    list_filter = ['status', 'phone_verified']
    search_fields = ['worker__full_name', 'worker__phone_number']
    readonly_fields = ['id_photo_preview', 'selfie_preview', 'submitted_at']
    actions = ['approve_verifications', 'reject_verifications']

    def id_photo_preview(self, obj):
        from django.utils.html import format_html
        if obj.id_photo:
            return format_html(
                '<img src="{}" width="300" style="border-radius:8px"/>',
                obj.id_photo)
        return 'No photo'
    id_photo_preview.short_description = 'ID Photo'

    def selfie_preview(self, obj):
        from django.utils.html import format_html
        if obj.selfie_photo:
            return format_html(
                '<img src="{}" width="300" style="border-radius:8px"/>',
                obj.selfie_photo)
        return 'No selfie'
    selfie_preview.short_description = 'Selfie'

    def approve_verifications(self, request, queryset):
        from django.utils import timezone
        for vr in queryset:
            vr.status = 'approved'
            vr.reviewed_at = timezone.now()
            vr.save()
            wp = vr.worker.worker_profile
            wp.verification_status = 'verified'
            wp.verified_at = timezone.now()
            wp.save()
            from notifications.utils import notify_user
            notify_user(
                recipient=vr.worker,
                notification_type='verification_approved',
                title='Verification Approved! ✅',
                body='Your account is now verified!',
            )
    approve_verifications.short_description = 'Approve selected'

    def reject_verifications(self, request, queryset):
        from django.utils import timezone
        for vr in queryset:
            vr.status = 'rejected'
            vr.reviewed_at = timezone.now()
            vr.save()
            wp = vr.worker.worker_profile
            wp.verification_status = 'rejected'
            wp.save()
    reject_verifications.short_description = 'Reject selected'


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'is_verified', 'created_at']
    list_filter = ['is_verified']

@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'is_verified', 'created_at']
    list_filter = ['is_verified']
    search_fields = ['user__email', 'user__full_name']
    actions = ['manually_verify']

    def manually_verify(self, request, queryset):
        for ev in queryset:
            ev.is_verified = True
            ev.save()
            ev.user.is_email_verified = True
            ev.user.is_active = True
            ev.user.save()
    manually_verify.short_description = 'Manually verify selected'    