from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, WorkerProfile, WorkerPortfolio, SavedWorker, VerificationRequest


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'full_name', 'phone_number', 'role', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        if user.role == 'worker':
            WorkerProfile.objects.create(user=user)
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'phone_number', 'role',
                  'profile_photo', 'district', 'sector', 'latitude', 'longitude']


class WorkerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    portfolio = serializers.SerializerMethodField()

    class Meta:
        model = WorkerProfile
        fields = '__all__'

    def get_portfolio(self, obj):
        return WorkerPortfolioSerializer(obj.portfolio.all(), many=True).data


class WorkerPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerPortfolio
        fields = ['id', 'image', 'description', 'uploaded_at']


class SavedWorkerSerializer(serializers.ModelSerializer):
    worker = WorkerProfileSerializer(read_only=True)

    class Meta:
        model = SavedWorker
        fields = '__all__'

class VerificationRequestSerializer(serializers.ModelSerializer):
    worker_name = serializers.CharField(
        source='worker.full_name', read_only=True)
    worker_phone = serializers.CharField(
        source='worker.phone_number', read_only=True)
    worker_district = serializers.CharField(
        source='worker.district', read_only=True)

    class Meta:
        model = VerificationRequest
        fields = '__all__'        