from rest_framework import serializers
from .models import (
    Job, JobApplication, Review, JobCategory, Report,
    JobActivity, JobCompletionProof,
)
from users.serializers import UserSerializer, WorkerProfileSerializer


class JobCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobCategory
        fields = '__all__'


class JobSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True)
    worker = WorkerProfileSerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    completion_proof = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = '__all__'

    def get_completion_proof(self, obj):
        try:
            proof = obj.completion_proof
        except JobCompletionProof.DoesNotExist:
            return None
        return JobCompletionProofSerializer(proof).data


class CreateJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        exclude = ['client', 'worker', 'status', 'payment_status']
        extra_kwargs = {
            'budget': {'required': False, 'allow_null': True},
            'latitude': {'required': False, 'allow_null': True},
            'longitude': {'required': False, 'allow_null': True},
            'scheduled_date': {'required': False, 'allow_null': True},
            'work_end_date': {'required': False, 'allow_null': True},
            'description': {'required': False, 'allow_blank': True},
        }

    def validate(self, attrs):
        start = attrs.get('scheduled_date')
        end = attrs.get('work_end_date')
        if start and end and end < start:
            raise serializers.ValidationError(
                {'work_end_date': 'End date must be on or after start date.'})
        return attrs


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
    reported_user = UserSerializer(read_only=True)

    class Meta:
        model = Report
        fields = '__all__'


class CreateReportSerializer(serializers.ModelSerializer):
    evidence_urls = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )

    class Meta:
        model = Report
        fields = ['reported_user', 'job', 'reason', 'description', 'evidence_urls']


class JobActivitySerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(
        source='actor.full_name', read_only=True, default='System')

    class Meta:
        model = JobActivity
        fields = [
            'id', 'event_type', 'message', 'actor_name', 'created_at',
        ]


class JobCompletionProofSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobCompletionProof
        fields = ['completion_note', 'photo_urls', 'submitted_at']


class SubmitCompletionProofSerializer(serializers.Serializer):
    completion_note = serializers.CharField(
        required=False, allow_blank=True, default='')
    photo_urls = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )

    def validate(self, attrs):
        note = (attrs.get('completion_note') or '').strip()
        urls = attrs.get('photo_urls') or []
        if not note and not urls:
            raise serializers.ValidationError(
                'Add a note and/or photo.')
        attrs['completion_note'] = note
        return attrs


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