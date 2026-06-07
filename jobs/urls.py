from django.urls import path
from .views import (
    JobListCreateView, JobDetailView, UpdateJobStatusView,
    NearbyWorkersView, JobApplicationView, AcceptApplicationView,
    RejectApplicationView, ReviewCreateView, JobCategoryListView,
    ReportCreateView, MyReportsListView, ClientJobApplicationsView,
    PublicJobListView, WorkerApplicationsView, ClientMyJobsView,
    JobTimelineView, SubmitCompletionProofView, ReleasePaymentView,
)

urlpatterns = [
    path('categories/', JobCategoryListView.as_view(), name='job_categories'),
    path('public/', PublicJobListView.as_view(), name='public_jobs'),
    path('mine/', ClientMyJobsView.as_view(), name='my_jobs'),
    path('', JobListCreateView.as_view(), name='jobs'),
    path('<int:pk>/', JobDetailView.as_view(), name='job_detail'),
    path('<int:pk>/status/', UpdateJobStatusView.as_view(), name='job_status'),
    path('<int:job_id>/apply/', JobApplicationView.as_view(), name='job_apply'),
    path('<int:job_id>/applications/', ClientJobApplicationsView.as_view(), name='job_applications'),
    path('applications/<int:pk>/accept/', AcceptApplicationView.as_view(), name='accept_application'),
    path('applications/<int:pk>/reject/', RejectApplicationView.as_view(), name='reject_application'),
    path('<int:job_id>/review/', ReviewCreateView.as_view(), name='job_review'),
    path('<int:job_id>/timeline/', JobTimelineView.as_view(), name='job_timeline'),
    path('<int:job_id>/completion-proof/', SubmitCompletionProofView.as_view(), name='completion_proof'),
    path('<int:job_id>/release-payment/', ReleasePaymentView.as_view(), name='release_payment'),
    path('nearby-workers/', NearbyWorkersView.as_view(), name='nearby_workers'),
    path('report/', ReportCreateView.as_view(), name='report'),
    path('my-reports/', MyReportsListView.as_view(), name='my_reports'),
    path('my-applications/', WorkerApplicationsView.as_view(), name='my_applications'),

]