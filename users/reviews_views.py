from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from jobs.models import Review
from jobs.serializers import ReviewSerializer


class UserReviewsView(APIView):
    """Public reviews received by a user (worker or client)."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        reviews = (
            Review.objects.filter(reviewee_id=user_id)
            .select_related('reviewer', 'job')
            .order_by('-created_at')[:20]
        )
        return Response(ReviewSerializer(reviews, many=True).data)
