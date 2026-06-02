from django.urls import path
from .views import ConversationListView, StartConversationView, MessageListView, SendMessageView

urlpatterns = [
    path('', ConversationListView.as_view(), name='conversations'),
    path('start/', StartConversationView.as_view(), name='start_conversation'),
    path('<int:conversation_id>/messages/', MessageListView.as_view(), name='messages'),
    path('<int:conversation_id>/send/', SendMessageView.as_view(), name='send_message'),
]