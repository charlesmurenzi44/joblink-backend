from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, WorkerProfile, WorkerPortfolio, SavedWorker, VerificationRequest


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'full_name', 'phone_number', 'role', 'password', 'password2']
        extra_kwargs = {
            'email': {'validators': []},
            'phone_number': {'validators': []},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match'})

        email = attrs['email'].strip()
        phone = attrs['phone_number'].strip()
        existing = User.objects.filter(email__iexact=email).first()

        if existing:
            if existing.is_active and existing.is_email_verified:
                raise serializers.ValidationError({
                    'email': 'This email is already registered. Please log in instead.',
                })
            if User.objects.filter(phone_number=phone).exclude(pk=existing.pk).exists():
                raise serializers.ValidationError({
                    'phone_number': (
                        'This phone number is already in use by another account.'
                    ),
                })
            attrs['_existing_unverified_user'] = existing
            return attrs

        if User.objects.filter(phone_number=phone).exists():
            raise serializers.ValidationError({
                'phone_number': (
                    'This phone number is already registered. '
                    'Try logging in or use a different number.'
                ),
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        existing = validated_data.pop('_existing_unverified_user', None)
        password = validated_data.pop('password')

        if existing:
            existing.full_name = validated_data['full_name']
            existing.phone_number = validated_data['phone_number']
            existing.role = validated_data['role']
            existing.set_password(password)
            existing.is_active = False
            existing.is_email_verified = False
            existing.save()
            if existing.role == 'worker':
                WorkerProfile.objects.get_or_create(user=existing)
            return existing

        user = User.objects.create_user(password=password, **validated_data)
        if user.role == 'worker':
            WorkerProfile.objects.create(user=user)
        return user


class UserSerializer(serializers.ModelSerializer):
    has_profile_photo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'phone_number', 'role',
                  'profile_photo', 'has_profile_photo', 'district', 'sector',
                  'cell', 'village',
                  'latitude', 'longitude', 'is_staff', 'is_active',
                  'employer_average_rating', 'employer_total_reviews']

    def get_has_profile_photo(self, obj):
        from .profile_utils import user_has_profile_photo
        return user_has_profile_photo(obj)


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