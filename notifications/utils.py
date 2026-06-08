def notify_user(recipient, notification_type: str, title: str, body: str, data: dict = None):
    """Create in-app notification AND send push notification"""
    from .models import Notification
    from .firebase import send_push_to_user

    # Save in-app notification
    Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        body=body,
        data=data or {},
    )

    # Send push notification
    send_push_to_user(recipient, title, body, data or {})