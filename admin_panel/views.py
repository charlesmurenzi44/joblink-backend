from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db.models import Q
from users.models import VerificationRequest
from jobs.models import Job, Report, JobApplication
from jobs.serializers import ReportSerializer
from jobs.activity import log_job_activity
from notifications.utils import notify_user

User = get_user_model()


class IsStaffUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )


class AdminStatsView(APIView):
    permission_classes = [IsStaffUser]

    def get(self, request):
        return Response({
            'users_total': User.objects.count(),
            'workers_total': User.objects.filter(role='worker').count(),
            'clients_total': User.objects.filter(role='client').count(),
            'jobs_total': Job.objects.count(),
            'jobs_active': Job.objects.filter(
                status__in=['posted', 'accepted', 'in_progress'],
            ).count(),
            'jobs_completed': Job.objects.filter(status='completed').count(),
            'pending_disputes': Report.objects.filter(
                status='pending',
            ).count(),
            'pending_verifications': VerificationRequest.objects.filter(
                status='pending',
            ).count(),
            'applications_total': JobApplication.objects.count(),
        })


class AdminReportListView(APIView):
    permission_classes = [IsStaffUser]

    def get(self, request):
        status_filter = request.query_params.get('status', 'pending')
        qs = Report.objects.select_related(
            'reporter', 'reported_user', 'job',
        ).order_by('-created_at')
        if status_filter != 'all':
            qs = qs.filter(status=status_filter)
        return Response(ReportSerializer(qs, many=True).data)


class AdminResolveReportView(APIView):
    permission_classes = [IsStaffUser]

    def post(self, request, pk):
        try:
            report = Report.objects.select_related(
                'job', 'reporter', 'reported_user',
            ).get(pk=pk)
        except Report.DoesNotExist:
            return Response({'error': 'Report not found'}, status=404)

        action = request.data.get('action')
        note = request.data.get('note', '').strip()
        payment_action = request.data.get('payment_action', 'none')

        if action not in ('resolve', 'dismiss'):
            return Response(
                {'error': 'action must be resolve or dismiss'},
                status=400,
            )

        report.status = 'resolved' if action == 'resolve' else 'dismissed'
        report.save(update_fields=['status'])

        job = report.job
        if job:
            if payment_action == 'release' and job.payment_status == 'disputed':
                job.payment_status = 'released'
                job.save(update_fields=['payment_status'])
                log_job_activity(
                    job,
                    request.user,
                    'payment_released',
                    'Admin released payment after dispute resolution.',
                )
            elif payment_action == 'refund' and job.payment_status == 'disputed':
                job.payment_status = 'unpaid'
                job.save(update_fields=['payment_status'])
                log_job_activity(
                    job,
                    request.user,
                    'payment_held',
                    'Admin refunded client after dispute resolution.',
                )

            log_job_activity(
                job,
                request.user,
                'dispute_resolved',
                f'Dispute {report.status} by admin. {note}'.strip(),
            )

        job_title = job.title if job else 'a user'
        body = f'Your report regarding "{job_title}" was {report.status}.'
        if note:
            body += f' Note: {note}'

        notify_user(
            recipient=report.reporter,
            notification_type='review_received',
            title=f'Dispute {report.status.title()}',
            body=body,
            data={'job_id': str(job.id)} if job else {},
        )
        notify_user(
            recipient=report.reported_user,
            notification_type='review_received',
            title=f'Dispute {report.status.title()}',
            body=body,
            data={'job_id': str(job.id)} if job else {},
        )

        return Response(ReportSerializer(report).data)


class AdminUserListView(APIView):
    permission_classes = [IsStaffUser]

    def get(self, request):
        from users.serializers import UserSerializer

        qs = User.objects.all().order_by('-date_joined')
        search = (request.query_params.get('search') or '').strip()
        role = request.query_params.get('role')
        if search:
            qs = qs.filter(
                Q(full_name__icontains=search)
                | Q(email__icontains=search)
                | Q(phone_number__icontains=search),
            )
        if role in ('client', 'worker'):
            qs = qs.filter(role=role)
        return Response(UserSerializer(qs[:200], many=True).data)


class AdminUserManageView(APIView):
    permission_classes = [IsStaffUser]

    def post(self, request, pk):
        from users.serializers import UserSerializer

        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        action = request.data.get('action')
        if action == 'ban':
            user.is_active = False
            user.save(update_fields=['is_active'])
        elif action == 'activate':
            user.is_active = True
            user.save(update_fields=['is_active'])
        elif action == 'promote_staff':
            user.is_staff = True
            user.save(update_fields=['is_staff'])
        elif action == 'demote_staff':
            if user.is_superuser:
                return Response(
                    {'error': 'Cannot demote superuser'},
                    status=400,
                )
            user.is_staff = False
            user.save(update_fields=['is_staff'])
        else:
            return Response(
                {'error': 'action must be ban, activate, promote_staff, or demote_staff'},
                status=400,
            )

        return Response(UserSerializer(user).data)
