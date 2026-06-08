from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q
from math import radians, sin, cos, sqrt, atan2
from users.models import WorkerProfile, User
from users.serializers import WorkerProfileSerializer
from notifications.utils import notify_user
from .models import Job, JobApplication, Review, JobCategory, Report, JobCompletionProof
from .activity import log_job_activity
from .serializers import (
    JobSerializer,
    CreateJobSerializer,
    JobApplicationSerializer,
    CreateApplicationSerializer,
    ReviewSerializer,
    CreateReviewSerializer,
    JobCategorySerializer,
    ReportSerializer,
    CreateReportSerializer,
    JobActivitySerializer,
    JobCompletionProofSerializer,
    SubmitCompletionProofSerializer,
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


JOB_NOTIFY_RADIUS_KM = 50


def worker_matches_job(worker, job, radius_km=JOB_NOTIFY_RADIUS_KM):
    """True if worker is in the same area as the job."""
    user = worker.user
    if job.district and user.district:
        if user.district.lower() == job.district.lower():
            return True
    if (job.latitude and job.longitude and
            user.latitude and user.longitude):
        distance = haversine_distance(
            job.latitude, job.longitude,
            user.latitude, user.longitude,
        )
        return distance <= radius_km
    return False


def worker_matches_job_skill(worker, job):
    """True if worker skill matches the job category."""
    if not job.category:
        return True
    if not worker.skill_category:
        return False
    return (
        worker.skill_category.lower() == job.category.name.lower()
        or job.category.name.lower() in worker.skill_category.lower()
        or worker.skill_category.lower() in job.category.name.lower()
    )


def notify_matching_workers_for_job(job):
    """In-app + push alerts for nearby workers with matching skills."""
    from notifications.firebase import send_push_to_nearby_workers

    workers = WorkerProfile.objects.filter(
        is_available=True,
        user__is_active=True,
        user__role='worker',
        user__is_email_verified=True,
    ).select_related('user')

    notified = 0
    for worker in workers:
        if not worker_matches_job_skill(worker, job):
            continue
        if not worker_matches_job(worker, job):
            continue

        category = job.category.name if job.category else 'work'
        notify_user(
            recipient=worker.user,
            notification_type='job_posted',
            title='New job near you! 💼',
            body=(
                f'"{job.title}" ({category}) in {job.district} '
                f'matches your skills.'
            ),
            data={'job_id': str(job.id)},
        )
        notified += 1

    try:
        send_push_to_nearby_workers(
            district=job.district,
            skill=job.category.name if job.category else None,
            title='New Job Near You! 💼',
            body=f'{job.title} posted in {job.district}',
            data={'job_id': str(job.id)},
        )
    except Exception:
        pass

    return notified


# ── Categories ────────────────────────────────────────────────

class JobCategoryListView(generics.ListAPIView):
    serializer_class = JobCategorySerializer
    permission_classes = [permissions.AllowAny]
    queryset = JobCategory.objects.all()


# ── Jobs ──────────────────────────────────────────────────────

class ClientMyJobsView(generics.ListAPIView):
    """Client's own posted jobs — always returns a JSON array."""
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role != 'client':
            return Job.objects.none()
        return Job.objects.filter(client=user).order_by('-created_at')


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

    def create(self, request, *args, **kwargs):
        if request.user.role != 'client':
            return Response(
                {'error': 'Only clients can post jobs.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        from users.profile_utils import ensure_profile_photo
        ensure_profile_photo(request.user)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        job = serializer.save(client=self.request.user)
        log_job_activity(
            job,
            self.request.user,
            'posted',
            f'Job "{job.title}" was posted in {job.district}.',
        )
        notify_matching_workers_for_job(job)


class PublicJobListView(generics.ListAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Job.objects.filter(status='posted')
        params = self.request.query_params

        category = params.get('category')
        if category:
            queryset = queryset.filter(category__name__icontains=category)

        district = params.get('district')
        if district:
            queryset = queryset.filter(district__icontains=district)

        min_budget = params.get('min_budget')
        if min_budget:
            queryset = queryset.filter(budget__gte=min_budget)

        max_budget = params.get('max_budget')
        if max_budget:
            queryset = queryset.filter(budget__lte=max_budget)

        if params.get('emergency') == 'true':
            queryset = queryset.filter(is_emergency=True)

        scheduled_after = params.get('scheduled_after')
        if scheduled_after:
            queryset = queryset.filter(scheduled_date__gte=scheduled_after)

        scheduled_before = params.get('scheduled_before')
        if scheduled_before:
            queryset = queryset.filter(scheduled_date__lte=scheduled_before)

        return queryset.order_by('-created_at')


class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Job.objects.select_related(
        'client', 'worker', 'worker__user', 'category', 'completion_proof',
    ).all()


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

        if job.client != request.user:
            return Response(
                {'error': 'Only the job owner can update status'},
                status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status')
        if new_status not in self.VALID_STATUSES:
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST)

        job.status = new_status
        job.save()

        if new_status == 'in_progress':
            log_job_activity(
                job, request.user, 'started',
                f'Work started on "{job.title}".',
            )
        elif new_status == 'completed':
            log_job_activity(
                job, request.user, 'completed',
                f'"{job.title}" marked as completed.',
            )
        elif new_status == 'cancelled':
            log_job_activity(
                job, request.user, 'cancelled',
                f'"{job.title}" was cancelled.',
            )

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
                body=(
                    f'"{job.title}" is complete. '
                    f'Please rate your employer!'
                ),
                data={'job_id': str(job.id)},
            )
            notify_user(
                recipient=job.client,
                notification_type='job_completed',
                title='Job Completed! 🎉',
                body=(
                    f'"{job.title}" is complete. '
                    f'Please rate your worker!'
                ),
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
        min_rating = request.query_params.get('min_rating')
        verified_only = request.query_params.get('verified_only') == 'true'

        if not lat or not lon:
            return Response(
                {'error': 'lat and lon are required'},
                status=400)

        workers = WorkerProfile.objects.filter(
            is_available=True,
        ).select_related('user')

        if verified_only:
            workers = workers.filter(verification_status='verified')

        if min_rating:
            try:
                workers = workers.filter(
                    average_rating__gte=float(min_rating))
            except ValueError:
                pass

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

        if user.role != 'worker':
            raise PermissionDenied('Only workers can apply for jobs.')

        from users.profile_utils import ensure_profile_photo
        ensure_profile_photo(user)

        if not user.is_active or not user.is_email_verified:
            raise PermissionDenied(
                'Verify your email before applying for jobs.')

        wp, _ = WorkerProfile.objects.get_or_create(user=user)
        if not wp.skill_category:
            raise PermissionDenied(
                'Complete your worker profile before applying.')

        if wp.verification_status != 'verified':
            raise PermissionDenied(
                'Complete ID verification before applying for jobs.')

        job = Job.objects.get(pk=self.kwargs['job_id'])

        # Check if already applied
        if JobApplication.objects.filter(
                job=job,
                worker=wp).exists():
            raise ValidationError(
                {'detail': 'You already applied for this job'})

        serializer.save(
            worker=wp,
            job=job,
        )

        log_job_activity(
            job,
            user,
            'application_received',
            f'{user.full_name} applied for this job.',
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

        if application.job.client != request.user:
            return Response(
                {'error': 'Only the job owner can accept applications'},
                status=403)

        application.status = 'accepted'
        application.save()

        job = application.job
        job.worker = application.worker
        job.status = 'accepted'
        job.payment_status = 'held'
        job.save()

        budget = f'{job.budget:.0f} RWF' if job.budget else 'the agreed amount'
        log_job_activity(
            job,
            request.user,
            'worker_hired',
            f'{application.worker.user.full_name} was hired.',
        )
        log_job_activity(
            job,
            request.user,
            'payment_held',
            f'Payment ({budget}) held in escrow until job completion.',
        )

        if job.payment_method == 'momo' and job.budget:
            from .momo_utils import request_collection, MoMoError
            try:
                request_collection(
                    job,
                    job.client.phone_number,
                    job.budget,
                )
            except MoMoError as exc:
                print(f'MoMo collection note: {exc}')

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


class RejectApplicationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            application = JobApplication.objects.get(pk=pk)
        except JobApplication.DoesNotExist:
            return Response(
                {'error': 'Application not found'},
                status=404)

        if application.job.client != request.user:
            return Response(
                {'error': 'Only the job owner can reject applications'},
                status=403)

        application.status = 'rejected'
        application.save()

        notify_user(
            recipient=application.worker.user,
            notification_type='new_application',
            title='Application Update',
            body=f'Your application for "{application.job.title}" was not selected.',
            data={'job_id': str(application.job.id)},
        )

        return Response(JobApplicationSerializer(application).data)


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
        user = self.request.user

        if job.status != 'completed':
            raise ValidationError(
                {'detail': 'You can only review completed jobs.'})

        if user == job.client:
            if job.worker is None:
                raise ValidationError(
                    {'detail': 'This job has no hired worker to review.'})
            reviewee = job.worker.user
        elif (hasattr(user, 'worker_profile') and
              job.worker_id == user.worker_profile.id):
            reviewee = job.client
        else:
            raise PermissionDenied(
                'Only the client or hired worker can review this job.')

        reviewee_id = self.request.data.get('reviewee')
        if reviewee_id and int(reviewee_id) != reviewee.id:
            raise ValidationError({'reviewee': 'Invalid reviewee for this job.'})

        if Review.objects.filter(job=job, reviewer=user).exists():
            raise ValidationError(
                {'detail': 'You already reviewed this job'})

        review = serializer.save(
            reviewer=user,
            reviewee=reviewee,
            job=job,
        )

        if reviewee.role == 'worker':
            profile = reviewee.worker_profile
            all_reviews = Review.objects.filter(reviewee=reviewee)
            count = all_reviews.count()
            profile.average_rating = (
                sum(r.rating for r in all_reviews) / count)
            profile.total_reviews = count
            profile.total_jobs_done = count
            profile.save()
        else:
            all_reviews = Review.objects.filter(reviewee=reviewee)
            count = all_reviews.count()
            reviewee.employer_average_rating = (
                sum(r.rating for r in all_reviews) / count)
            reviewee.employer_total_reviews = count
            reviewee.save(update_fields=[
                'employer_average_rating', 'employer_total_reviews',
            ])

        notify_user(
            recipient=reviewee,
            notification_type='review_received',
            title='New Review! ⭐',
            body=f'{user.full_name} gave you {review.rating} stars.',
            data={'job_id': str(job.id)},
        )

        log_job_activity(
            job,
            user,
            'reviewed',
            f'{user.full_name} left a {review.rating}-star review.',
        )


# ── Timeline & escrow ─────────────────────────────────────────

class JobTimelineView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, job_id):
        try:
            job = Job.objects.get(pk=job_id)
        except Job.DoesNotExist:
            return Response({'error': 'Job not found'}, status=404)

        user = request.user
        is_participant = (
            job.client == user or
            (hasattr(user, 'worker_profile') and
             job.worker_id == user.worker_profile.id)
        )
        if not is_participant and user.role != 'client':
            if job.status != 'posted':
                return Response({'error': 'Not allowed'}, status=403)

        activities = job.activities.all()
        return Response(JobActivitySerializer(activities, many=True).data)


class SubmitCompletionProofView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, job_id):
        try:
            job = Job.objects.get(pk=job_id)
        except Job.DoesNotExist:
            return Response({'error': 'Job not found'}, status=404)

        is_client = job.client == request.user
        is_worker = (
            hasattr(request.user, 'worker_profile')
            and job.worker_id == request.user.worker_profile.id
        )
        if not (is_client or is_worker or request.user.is_staff):
            return Response({'error': 'Not allowed'}, status=403)

        try:
            proof = job.completion_proof
        except JobCompletionProof.DoesNotExist:
            return Response({'error': 'No completion proof yet'}, status=404)

        return Response(JobCompletionProofSerializer(proof).data)

    def post(self, request, job_id):
        try:
            job = Job.objects.get(pk=job_id)
        except Job.DoesNotExist:
            return Response({'error': 'Job not found'}, status=404)

        if not hasattr(request.user, 'worker_profile'):
            return Response({'error': 'Workers only'}, status=403)

        if job.worker_id != request.user.worker_profile.id:
            return Response({'error': 'Not your job'}, status=403)

        if job.status not in ('accepted', 'in_progress'):
            return Response(
                {'error': 'Submit proof when job is active'},
                status=400)

        note = (request.data.get('completion_note') or '').strip()
        photo_urls = []

        existing = JobCompletionProof.objects.filter(job=job).first()
        if existing and existing.photo_urls:
            photo_urls = list(existing.photo_urls)

        photo_file = request.FILES.get('photo')
        if photo_file:
            try:
                from users.media_utils import upload_image
                url = upload_image(
                    photo_file,
                    folder='joblink/completion',
                    public_id=f'job_{job_id}_worker_{request.user.id}',
                    transformation=[
                        {'width': 1200, 'height': 1200,
                         'crop': 'limit', 'quality': 'auto'},
                    ],
                )
                photo_urls.append(url)
            except ValueError as exc:
                return Response({'error': str(exc)}, status=503)
            except Exception as exc:
                return Response(
                    {'error': f'Photo upload failed: {exc}'},
                    status=500,
                )

        if request.content_type and 'application/json' in request.content_type:
            ser = SubmitCompletionProofSerializer(data=request.data)
            ser.is_valid(raise_exception=True)
            note = ser.validated_data.get('completion_note', '').strip()
            extra_urls = ser.validated_data.get('photo_urls') or []
            photo_urls.extend(extra_urls)

        if not note and not photo_urls:
            return Response(
                {'error': 'Add a short note and/or an optional photo.'},
                status=400,
            )

        proof, _ = JobCompletionProof.objects.update_or_create(
            job=job,
            defaults={
                'worker': job.worker,
                'completion_note': note,
                'photo_urls': photo_urls,
            },
        )

        log_job_activity(
            job,
            request.user,
            'completion_submitted',
            'Worker submitted completion proof.',
        )

        notify_user(
            recipient=job.client,
            notification_type='job_update',
            title='Work proof submitted',
            body=f'{request.user.full_name} submitted proof for "{job.title}".',
            data={'job_id': str(job.id)},
        )

        return Response(JobCompletionProofSerializer(proof).data)


class ReleasePaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, job_id):
        try:
            job = Job.objects.get(pk=job_id)
        except Job.DoesNotExist:
            return Response({'error': 'Job not found'}, status=404)

        if job.client != request.user:
            return Response({'error': 'Only the client can release payment'}, status=403)

        if job.status != 'completed':
            return Response(
                {'error': 'Job must be completed first'},
                status=400)

        if job.payment_status == 'released':
            return Response({'message': 'Payment already released'})

        if job.payment_status == 'disputed':
            return Response(
                {'error': 'Payment is under dispute'},
                status=400)

        job.payment_status = 'released'
        job.save(update_fields=['payment_status'])

        worker_name = job.worker.user.full_name if job.worker else 'worker'
        budget = f'{job.budget:.0f} RWF' if job.budget else 'Payment'
        log_job_activity(
            job,
            request.user,
            'payment_released',
            f'{budget} released to {worker_name}.',
        )

        if job.payment_method == 'momo' and job.budget and job.worker:
            from .momo_utils import request_disbursement, MoMoError
            try:
                request_disbursement(
                    job,
                    job.worker.user.phone_number,
                    job.budget,
                )
            except MoMoError as exc:
                print(f'MoMo disbursement note: {exc}')

        if job.worker:
            notify_user(
                recipient=job.worker.user,
                notification_type='job_completed',
                title='Payment released 💰',
                body=f'Payment for "{job.title}" was released to you.',
                data={'job_id': str(job.id)},
            )

        return Response(JobSerializer(job).data)


# ── Reports & disputes ────────────────────────────────────────

class MyReportsListView(generics.ListAPIView):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Report.objects.filter(
            Q(reporter=user) | Q(reported_user=user)
        ).select_related(
            'reporter', 'reported_user', 'job',
        ).order_by('-created_at')


class ReportCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        data = request.data.copy()
        evidence_urls = []

        photo = request.FILES.get('photo')
        if photo:
            try:
                from users.media_utils import upload_image
                url = upload_image(
                    photo,
                    folder='joblink/disputes',
                    public_id=f'dispute_{request.user.id}',
                )
                evidence_urls.append(url)
            except ValueError as exc:
                return Response({'error': str(exc)}, status=503)

        if request.content_type and 'application/json' in request.content_type:
            extra = data.get('evidence_urls') or []
            if isinstance(extra, list):
                evidence_urls.extend(extra)

        ser = CreateReportSerializer(data={
            'reported_user': data.get('reported_user'),
            'job': data.get('job'),
            'reason': data.get('reason', 'other'),
            'description': data.get('description', ''),
            'evidence_urls': evidence_urls,
        })
        ser.is_valid(raise_exception=True)
        report = ser.save(reporter=request.user)

        job = report.job
        if job:
            job.payment_status = 'disputed'
            job.save(update_fields=['payment_status'])
            log_job_activity(
                job,
                request.user,
                'dispute_opened',
                f'Dispute opened: {report.get_reason_display()}.',
            )
            notify_user(
                recipient=report.reported_user,
                notification_type='new_application',
                title='Dispute opened',
                body=(
                    f'A dispute was opened regarding "{job.title}". '
                    f'Our team will review it.'
                ),
                data={'job_id': str(job.id)},
            )

        return Response(ReportSerializer(report).data, status=201)