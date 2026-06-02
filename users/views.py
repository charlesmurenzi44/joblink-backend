from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
import uuid
import cloudinary.uploader

from .models import (
    User, WorkerProfile, WorkerPortfolio,
    SavedWorker, OTPVerification, VerificationRequest,
    EmailVerification,
)
from .otp import generate_otp, is_otp_valid
from .email_utils import (
    generate_code, send_verification_email,
    send_welcome_email,
)
from .serializers import (
    RegisterSerializer, UserSerializer,
    WorkerProfileSerializer, WorkerPortfolioSerializer,
    SavedWorkerSerializer, VerificationRequestSerializer,
)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        # Auto-set Kigali as default location
        if not user.latitude:
            user.latitude = -1.9441
            user.longitude = 30.0619
            user.district = 'Gasabo'
            user.save()


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(email=email, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            user_data = UserSerializer(user).data

            # Add verification status to response
            is_verified = False
            try:
                if user.role == 'worker':
                    is_verified = user.worker_profile.verification_status == 'verified'
                else:
                    # Clients are auto-verified for now
                    is_verified = True
                user_data['is_verified'] = is_verified
            except Exception:
                user_data['is_verified'] = False

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': user_data,
            })
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class WorkerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = WorkerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.worker_profile


class PortfolioUploadView(generics.CreateAPIView):
    serializer_class = WorkerPortfolioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(worker=self.request.user.worker_profile)


class SavedWorkerView(generics.ListCreateAPIView):
    serializer_class = SavedWorkerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedWorker.objects.filter(client=self.request.user)

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)

class MyReviewsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from jobs.models import Review
        from jobs.serializers import ReviewSerializer
        given = Review.objects.filter(
            reviewer=request.user
        ).select_related('reviewer', 'reviewee').order_by('-created_at')
        received = Review.objects.filter(
            reviewee=request.user
        ).select_related('reviewer', 'reviewee').order_by('-created_at')
        return Response({
            'given': ReviewSerializer(given, many=True).data,
            'received': ReviewSerializer(received, many=True).data,
        })


class UploadProfilePhotoView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get('photo')
        if not file:
            return Response(
                {'error': 'No photo provided'},
                status=400)
        try:
            result = cloudinary.uploader.upload(
                file,
                folder='joblink/profiles',
                public_id=f'user_{request.user.id}',
                overwrite=True,
                transformation=[
                    {'width': 400, 'height': 400,
                     'crop': 'fill', 'gravity': 'face'},
                ],
            )
            request.user.profile_photo = result['secure_url']
            request.user.save()
            return Response({
                'photo_url': result['secure_url'],
                'message': 'Photo uploaded successfully'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class UploadPortfolioPhotoView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get('image')
        description = request.data.get('description', '')
        if not file:
            return Response(
                {'error': 'No image provided'},
                status=400)
        try:
            result = cloudinary.uploader.upload(
                file,
                folder='joblink/portfolio',
                transformation=[
                    {'width': 800, 'height': 600,
                     'crop': 'fill'},
                ],
            )
            from .models import WorkerPortfolio
            portfolio = WorkerPortfolio.objects.create(
                worker=request.user.worker_profile,
                image=result['secure_url'],
                description=description,
            )
            from .serializers import WorkerPortfolioSerializer
            return Response(
                WorkerPortfolioSerializer(portfolio).data,
                status=201)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class DeletePortfolioPhotoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        try:
            from .models import WorkerPortfolio
            photo = WorkerPortfolio.objects.get(
                pk=pk,
                worker=request.user.worker_profile)
            photo.delete()
            return Response(
                {'message': 'Deleted successfully'})
        except Exception:
            return Response(
                {'error': 'Not found'}, status=404)        


class SendOTPView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        code = generate_otp()
        OTPVerification.objects.update_or_create(
            user=user,
            defaults={'code': code, 'is_verified': False},
        )
        # In production send via SMS (Africa's Talking etc)
        # For now print to console
        print(f"\n{'='*40}")
        print(f"OTP for {user.full_name}: {code}")
        print(f"{'='*40}\n")
        return Response({
            'message': f'OTP sent to {user.phone_number}',
            'dev_otp': code,  # remove in production
        })


class VerifyOTPView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        code = request.data.get('code')
        try:
            otp_obj = request.user.otp
        except OTPVerification.DoesNotExist:
            return Response(
                {'error': 'No OTP found. Request a new one.'},
                status=400)

        if not is_otp_valid(otp_obj):
            return Response(
                {'error': 'OTP expired. Request a new one.'},
                status=400)

        if otp_obj.code != code:
            return Response(
                {'error': 'Invalid OTP code'},
                status=400)

        otp_obj.is_verified = True
        otp_obj.save()

        # Update verification request
        try:
            vr = request.user.verification_request
            vr.phone_verified = True
            vr.save()
        except VerificationRequest.DoesNotExist:
            pass

        return Response({'message': 'Phone verified! ✅'})


class SubmitVerificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        user = request.user

        # Check phone is verified
        try:
            otp = user.otp
            if not otp.is_verified:
                return Response(
                    {'error': 'Please verify your phone first'},
                    status=400)
        except OTPVerification.DoesNotExist:
            return Response(
                {'error': 'Please verify your phone first'},
                status=400)

        id_photo = request.FILES.get('id_photo')
        selfie = request.FILES.get('selfie_photo')
        id_number = request.data.get('id_number', '')

        if not id_photo or not selfie:
            return Response(
                {'error': 'ID photo and selfie are required'},
                status=400)

        try:
            # Upload ID photo
            id_result = cloudinary.uploader.upload(
                id_photo,
                folder='joblink/verifications/ids',
                public_id=f'id_{user.id}',
                overwrite=True,
            )
            # Upload selfie
            selfie_result = cloudinary.uploader.upload(
                selfie,
                folder='joblink/verifications/selfies',
                public_id=f'selfie_{user.id}',
                overwrite=True,
            )

            VerificationRequest.objects.update_or_create(
                worker=user,
                defaults={
                    'id_photo': id_result['secure_url'],
                    'selfie_photo': selfie_result['secure_url'],
                    'id_number': id_number,
                    'phone_verified': True,
                    'status': 'pending',
                },
            )

            # Notify admin (create notification for superusers)
            from django.contrib.auth import get_user_model
            User = get_user_model()
            admins = User.objects.filter(is_staff=True)
            from notifications.models import Notification
            for admin in admins:
                Notification.objects.create(
                    recipient=admin,
                    notification_type='verification_approved',
                    title='New Verification Request 📋',
                    body=f'{user.full_name} submitted verification documents.',
                )

            return Response({
                'message': 'Verification submitted! We will review within 24 hours.'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class VerificationStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            vr = request.user.verification_request
            wp = request.user.worker_profile
            return Response({
                'status': vr.status,
                'phone_verified': vr.phone_verified,
                'submitted_at': vr.submitted_at,
                'admin_note': vr.admin_note,
                'verification_status': wp.verification_status,
            })
        except VerificationRequest.DoesNotExist:
            return Response({
                'status': 'not_submitted',
                'phone_verified': False,
                'verification_status': 'pending',
            })


class AdminVerificationListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from .serializers import VerificationRequestSerializer
        requests = VerificationRequest.objects.filter(
            status='pending'
        ).select_related('worker').order_by('-submitted_at')
        return Response(
            VerificationRequestSerializer(
                requests, many=True).data)


class AdminReviewVerificationView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        try:
            vr = VerificationRequest.objects.get(pk=pk)
        except VerificationRequest.DoesNotExist:
            return Response(
                {'error': 'Not found'}, status=404)

        action = request.data.get('action')
        note = request.data.get('note', '')

        if action not in ['approve', 'reject']:
            return Response(
                {'error': 'action must be approve or reject'},
                status=400)

        vr.status = (
            'approved' if action == 'approve'
            else 'rejected')
        vr.admin_note = note
        vr.reviewed_at = timezone.now()
        vr.save()

        # Update worker profile
        wp = vr.worker.worker_profile
        wp.verification_status = (
            'verified' if action == 'approve'
            else 'rejected')
        if action == 'approve':
            from django.utils import timezone as tz
            wp.verified_at = tz.now()
        wp.save()

        # Notify worker
        from notifications.utils import notify_user
        if action == 'approve':
            notify_user(
                recipient=vr.worker,
                notification_type='verification_approved',
                title='Verification Approved! ✅',
                body='Your account is now verified. You can start receiving job offers!',
            )
        else:
            notify_user(
                recipient=vr.worker,
                notification_type='verification_rejected',
                title='Verification Rejected ❌',
                body=f'Your verification was rejected. Reason: {note}. Please resubmit.',
            )

        return Response({
            'message': f'Worker {vr.status} successfully'
        })         



class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()

        # Set default location
        if not user.latitude:
            user.latitude = -1.9441
            user.longitude = 30.0619
            user.district = 'Gasabo'
            user.is_active = False  # inactive until verified
            user.save()

        # Create email verification
        code = generate_code()
        import uuid
        token = uuid.uuid4()
        EmailVerification.objects.update_or_create(
            user=user,
            defaults={
                'code': code,
                'token': token,
                'is_verified': False,
            }
        )

        # Send verification email
        send_verification_email(user, code, token)


class VerifyEmailCodeView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')

        try:
            user = User.objects.get(email=email)
            ev = user.email_verification
        except (User.DoesNotExist,
                EmailVerification.DoesNotExist):
            return Response(
                {'error': 'Invalid email or code'},
                status=400)

        # Check expiry (10 minutes)
        expiry = ev.created_at + timedelta(minutes=10)
        if timezone.now() > expiry:
            return Response(
                {'error': 'Code expired. Request a new one.'},
                status=400)

        if ev.code != code:
            return Response(
                {'error': 'Invalid code'},
                status=400)

        # Activate user
        ev.is_verified = True
        ev.save()
        user.is_email_verified = True
        user.is_active = True
        user.save()

        # Send welcome email
        send_welcome_email(user)

        return Response({
            'message': 'Email verified! You can now login. 🎉'
        })


class VerifyEmailTokenView(APIView):
    """Handles click from email link"""
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        try:
            ev = EmailVerification.objects.get(token=token)
        except EmailVerification.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired link'},
                status=400)

        if ev.is_verified:
            return Response(
                {'message': 'Already verified!'})

        # Check expiry
        expiry = ev.created_at + timedelta(minutes=10)
        if timezone.now() > expiry:
            return Response(
                {'error': 'Link expired. Request a new one.'},
                status=400)

        # Activate user
        ev.is_verified = True
        ev.save()
        ev.user.is_email_verified = True
        ev.user.is_active = True
        ev.user.save()

        send_welcome_email(ev.user)

        return Response({
            'message': 'Email verified successfully! 🎉 You can now login.'
        })


class ResendVerificationEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Email not found'},
                status=404)

        if user.is_email_verified:
            return Response(
                {'message': 'Email already verified'})

        import uuid
        code = generate_code()
        token = uuid.uuid4()
        EmailVerification.objects.update_or_create(
            user=user,
            defaults={
                'code': code,
                'token': token,
                'is_verified': False,
            }
        )
        send_verification_email(user, code, token)

        return Response({
            'message': f'Verification email resent to {email}'
        })       