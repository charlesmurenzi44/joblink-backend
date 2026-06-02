from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError, PermissionDenied
from math import radians, sin, cos, sqrt, atan2
from users.models import WorkerProfile, User
from users.serializers import WorkerProfileSerializer
from notifications.utils import notify_user
from .models import Job, JobApplication, Review, JobCategory, Report
from .serializers import (
    JobSerializer,
    CreateJobSerializer,
    JobApplicationSerializer,
    CreateApplicationSerializer,
    ReviewSerializer,
    CreateReviewSerializer,
    JobCategorySerializer,
    ReportSerializer,
)


# ── Helpers ───────────────────────────────────────────────────

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(
        radians, [float(lat1), float(lon1),
                  float(lat2), float(lon2)])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (sin(dlat/2)**2 +
         cos(lat1) * cos(lat2) * sin(dlon/2)**2)
    return R * 2 * atan2(sqrt(a), sqrt(1-a))


# ── Categories ────────────────────────────────────────────────

class JobCategoryListView(generics.ListAPIView):
    serializer_class = JobCategorySerializer
    permission_classes = [permissions.AllowAny]
    queryset = JobCategory.objects.all()


# ── Jobs ──────────────────────────────────────────────────────

class JobListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return (CreateJobSerializer
                if self.request.method == 'POST'
                else JobSerializer)

    def get_queryset(self):
        user = self.request.user
        queryset = (
            Job.objects.filter(client=user)
            if user.role == 'client'
            else Job.objects.filter(status='posted')
        )
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(
                category__name__icontains=category)
        district = self.request.query_params.get('district')
        if district:
            queryset = queryset.filter(
                district__icontains=district)
        if self.request.query_params.get('emergency') == 'true':
            queryset = queryset.filter(is_emergency=True)
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        job = serializer.save(client=self.request.user)
        try:
            from notifications.firebase import (
                send_push_to_nearby_workers)
            send_push_to_nearby_workers(
                district=job.district,
                title='New Job Near You! 💼',
                body=f'{job.title} posted in {job.district}',
                data={'job_id': str(job.id)},
            )
        except Exception:
            pass


class PublicJobListView(generics.ListAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Job.objects.filter(status='posted')
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(
                category__name__icontains=category)
        return queryset.order_by('-created_at')


class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Job.objects.all()


class UpdateJobStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    VALID_STATUSES = [
        'posted', 'accepted', 'in_progress',
        'completed', 'cancelled',
    ]

    def patch(self, request, pk):
        try:
            job = Job.objects.get(pk=pk)
        except Job.DoesNotExist:
            return Response(
                {'error': 'Job not found'},
                status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        if new_status not in self.VALID_STATUSES:
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST)

        job.status = new_status
        job.save()

        if job.worker and new_status == 'in_progress':
            notify_user(
                recipient=job.worker.user,
                notification_type='job_accepted',
                title='Job Started 🔨',
                body=f'"{job.title}" has been marked as in progress.',
                data={'job_id': str(job.id)},
            )

        if job.worker and new_status == 'completed':
            notify_user(
                recipient=job.worker.user,
                notification_type='job_completed',
                title='Job Completed! 🎉',
                body=f'"{job.title}" marked complete. Please leave a review!',
                data={'job_id': str(job.id)},
            )

        return Response(JobSerializer(job).data)


# ── Nearby Workers ────────────────────────────────────────────

class NearbyWorkersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        skill = request.query_params.get('skill')
        radius = float(request.query_params.get('radius', 50))
        district = request.query_params.get('district', '')

        if not lat or not lon:
            return Response(
                {'error': 'lat and lon are required'},
                status=400)

        workers = WorkerProfile.objects.filter(
            is_available=True,
        ).select_related('user')

        if skill:
            workers = workers.filter(
                skill_category__icontains=skill)

        nearby = []
        for worker in workers:
            if worker.user.latitude and worker.user.longitude:
                distance = haversine_distance(
                    lat, lon,
                    worker.user.latitude,
                    worker.user.longitude,
                )
                if distance <= radius:
                    nearby.append((distance, worker))
            elif (worker.user.district and district and
                  worker.user.district.lower() ==
                  district.lower()):
                nearby.append((0, worker))

        nearby.sort(key=lambda x: x[0])

        result = []
        for distance, worker in nearby:
            data = WorkerProfileSerializer(worker).data
            data['distance_km'] = round(distance, 2)
            result.append(data)

        return Response(result)


# ── Applications ──────────────────────────────────────────────

class JobApplicationView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return (CreateApplicationSerializer
                if self.request.method == 'POST'
                else JobApplicationSerializer)

    def get_queryset(self):
        return JobApplication.objects.filter(
            job_id=self.kwargs.get('job_id'))

    def perform_create(self, serializer):
        user = self.request.user

        # Check worker is verified
        if hasattr(user, 'worker_profile'):
            if user.worker_profile.verification_status != 'verified':
                raise PermissionDenied(
                    'Your account must be verified '
                    'before applying for jobs.')
        else:
            # Auto-create worker profile if missing
            WorkerProfile.objects.create(user=user)

        job = Job.objects.get(pk=self.kwargs['job_id'])

        # Check if already applied
        if JobApplication.objects.filter(
                job=job,
                worker=user.worker_profile).exists():
            raise ValidationError(
                {'detail': 'You already applied for this job'})

        serializer.save(
            worker=user.worker_profile,
            job=job,
        )

        notify_user(
            recipient=job.client,
            notification_type='new_application',
            title='New Application! 📋',
            body=f'{user.full_name} applied for "{job.title}"',
            data={'job_id': str(job.id)},
        )


class ClientJobApplicationsView(generics.ListAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JobApplication.objects.filter(
            job_id=self.kwargs['job_id'],
            job__client=self.request.user,
        )


class AcceptApplicationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            application = JobApplication.objects.get(pk=pk)
        except JobApplication.DoesNotExist:
            return Response(
                {'error': 'Application not found'},
                status=404)

        application.status = 'accepted'
        application.save()

        job = application.job
        job.worker = application.worker
        job.status = 'accepted'
        job.save()

        JobApplication.objects.filter(
            job=job).exclude(pk=pk).update(status='rejected')

        notify_user(
            recipient=application.worker.user,
            notification_type='job_accepted',
            title='You got hired! 🎉',
            body=f'Your application for "{job.title}" was accepted by {job.client.full_name}',
            data={'job_id': str(job.id)},
        )

        rejected_apps = JobApplication.objects.filter(
            job=job, status='rejected')
        for app in rejected_apps:
            notify_user(
                recipient=app.worker.user,
                notification_type='new_application',
                title='Application Update',
                body=f'Your application for "{job.title}" was not selected.',
                data={'job_id': str(job.id)},
            )

        return Response({'message': 'Worker hired successfully'})


class WorkerApplicationsView(generics.ListAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JobApplication.objects.filter(
            worker=self.request.user.worker_profile
        ).order_by('-applied_at')


# ── Reviews ───────────────────────────────────────────────────

class ReviewCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CreateReviewSerializer

    def perform_create(self, serializer):
        job = Job.objects.get(pk=self.kwargs['job_id'])
        reviewee_id = self.request.data.get('reviewee')
        reviewee = User.objects.get(pk=reviewee_id)

        if Review.objects.filter(
                job=job,
                reviewer=self.request.user).exists():
            raise ValidationError(
                {'detail': 'You already reviewed this job'})

        review = serializer.save(
            reviewer=self.request.user,
            reviewee=reviewee,
            job=job,
        )

        if reviewee.role == 'worker':
            profile = reviewee.worker_profile
            all_reviews = Review.objects.filter(
                reviewee=reviewee)
            count = all_reviews.count()
            profile.average_rating = (
                sum(r.rating for r in all_reviews) / count)
            profile.total_reviews = count
            profile.total_jobs_done = count
            profile.save()

        notify_user(
            recipient=reviewee,
            notification_type='review_received',
            title='New Review! ⭐',
            body=f'{self.request.user.full_name} gave you {review.rating} stars.',
            data={'job_id': str(job.id)},
        )


# ── Reports ───────────────────────────────────────────────────

class ReportCreateView(generics.CreateAPIView):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)