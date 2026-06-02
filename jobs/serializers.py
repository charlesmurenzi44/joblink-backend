from rest_framework import serializers
from .models import Job, JobApplication, Review, JobCategory, Report
from users.serializers import UserSerializer, WorkerProfileSerializer


class JobCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobCategory
        fields = '__all__'


class JobSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True)
    worker = WorkerProfileSerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Job
        fields = '__all__'


class CreateJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        exclude = ['client', 'worker', 'status']


class JobApplicationSerializer(serializers.ModelSerializer):
    worker = WorkerProfileSerializer(read_only=True)
    job = JobSerializer(read_only=True)              # ← was missing

    class Meta:
        model = JobApplication
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    reviewer = UserSerializer(read_only=True)

    class Meta:
        model = Review
        fields = '__all__'


class ReportSerializer(serializers.ModelSerializer):
    reporter = UserSerializer(read_only=True)

    class Meta:
        model = Report
        fields = '__all__'


class CreateApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = ['cover_note', 'proposed_rate']
        extra_kwargs = {
            'cover_note': {'required': False, 'allow_blank': True},
            'proposed_rate': {'required': False, 'allow_null': True},
        }


class CreateReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['rating', 'comment', 'reviewee']
        extra_kwargs = {
            'comment': {'required': False, 'allow_blank': True},
        }