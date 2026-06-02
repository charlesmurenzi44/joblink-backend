from rest_framework import serializers
from .models import Conversation, Message
from users.serializers import UserSerializer


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ['sender', 'conversation', 'is_read', 'sent_at']


class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = '__all__'

    def get_last_message(self, obj):
        last = obj.messages.order_by('-sent_at').first()
        return MessageSerializer(last).data if last else None