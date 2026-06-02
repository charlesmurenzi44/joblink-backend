from django.contrib import admin
from .models import Job, JobApplication, Review, JobCategory
from .models import Job, JobApplication, Review, JobCategory, Report


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']
    search_fields = ['name']


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'client', 'category', 'status', 'is_emergency', 'district', 'created_at']
    list_filter = ['status', 'is_emergency', 'payment_method', 'category']
    search_fields = ['title', 'client__full_name', 'district']
    ordering = ['-created_at']


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ['job', 'worker', 'status', 'proposed_rate', 'applied_at']
    list_filter = ['status']
    search_fields = ['job__title', 'worker__user__full_name']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['reviewer', 'reviewee', 'rating', 'job', 'created_at']
    list_filter = ['rating']

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'reported_user', 'reason', 'status', 'created_at']
    list_filter = ['reason', 'status']
    search_fields = ['reporter__full_name', 'reported_user__full_name']
    actions = ['mark_resolved', 'mark_dismissed']

    def mark_resolved(self, request, queryset):
        queryset.update(status='resolved')
    mark_resolved.short_description = 'Mark selected as resolved'

    def mark_dismissed(self, request, queryset):
        queryset.update(status='dismissed')
    mark_dismissed.short_description = 'Mark selected as dismissed'    