from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'conversation', 'message_type', 'is_read', 'sent_at']
    list_filter = ['message_type', 'is_read']
    search_fields = ['sender__full_name', 'content']