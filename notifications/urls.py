from django.urls import path
from .views import (NotificationListView, MarkNotificationReadView,
                    MarkAllReadView, SaveFCMTokenView, UnreadCountView)

urlpatterns = [
    path('', NotificationListView.as_view(), name='notifications'),
    path('<int:pk>/read/', MarkNotificationReadView.as_view(), name='mark_read'),
    path('read-all/', MarkAllReadView.as_view(), name='mark_all_read'),
    path('unread-count/', UnreadCountView.as_view(), name='unread_count'),
    path('fcm-token/', SaveFCMTokenView.as_view(), name='fcm_token'),
    path('fcm-token/', SaveFCMTokenView.as_view()),
]