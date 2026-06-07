from django.urls import path
from .views import (
    AdminStatsView,
    AdminReportListView,
    AdminResolveReportView,
    AdminUserListView,
    AdminUserManageView,
)

urlpatterns = [
    path('stats/', AdminStatsView.as_view(), name='admin_stats'),
    path('reports/', AdminReportListView.as_view(), name='admin_reports'),
    path(
        'reports/<int:pk>/resolve/',
        AdminResolveReportView.as_view(),
        name='admin_resolve_report',
    ),
    path('users/', AdminUserListView.as_view(), name='admin_users'),
    path(
        'users/<int:pk>/manage/',
        AdminUserManageView.as_view(),
        name='admin_user_manage',
    ),
]
