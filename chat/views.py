from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from users.models import User


class ConversationListView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.conversations.all().order_by('-created_at')


class StartConversationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        other_user_id = request.data.get('user_id')
        try:
            other_user = User.objects.get(pk=other_user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        # Check if conversation already exists
        conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=other_user
        ).first()

        if not conversation:
            conversation = Conversation.objects.create()
            conversation.participants.add(request.user, other_user)

        return Response(ConversationSerializer(conversation).data)


class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        # Mark messages as read
        Message.objects.filter(
            conversation_id=conversation_id,
            is_read=False
        ).exclude(sender=self.request.user).update(is_read=True)
        return Message.objects.filter(conversation_id=conversation_id).order_by('sent_at')


class SendMessageView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        conversation_id = self.kwargs['conversation_id']
        conversation = Conversation.objects.get(
            pk=conversation_id)
        serializer.save(
            sender=self.request.user,
            conversation=conversation,
            message_type=self.request.data.get(
                'message_type', 'text'),
        )