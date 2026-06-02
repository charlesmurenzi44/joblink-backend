import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import os


def _init_firebase():
    if not firebase_admin._apps:
        cred_path = settings.FIREBASE_CREDENTIALS
        if os.path.exists(cred_path):
            try:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print('Firebase initialized ✅')
            except Exception as e:
                print(f'Firebase init error: {e}')
        else:
            print(f'Firebase credentials not found: {cred_path}')


def send_push_notification(
        token: str,
        title: str,
        body: str,
        data: dict = None):
    """Send push notification to single device"""
    _init_firebase()
    if not firebase_admin._apps:
        return None
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data={k: str(v) for k, v in (data or {}).items()},
            token=token,
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    icon='notification_icon',
                    color='#00A651',
                    sound='default',
                ),
            ),
            webpush=messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    icon='/icons/Icon-192.png',
                    badge='/icons/Icon-192.png',
                ),
                fcm_options=messaging.WebpushFCMOptions(
                    link='/',
                ),
            ),
        )
        response = messaging.send(message)
        print(f'Push sent successfully: {response}')
        return response
    except messaging.UnregisteredError:
        # Token expired — remove it
        from notifications.models import FCMToken
        FCMToken.objects.filter(token=token).delete()
        print(f'Removed expired FCM token')
        return None
    except Exception as e:
        print(f'Push notification error: {e}')
        return None


def send_push_to_user(
        user,
        title: str,
        body: str,
        data: dict = None):
    """Send push to user by FCM token"""
    try:
        fcm = user.fcm_token
        if fcm and fcm.token:
            return send_push_notification(
                fcm.token, title, body, data)
    except Exception as e:
        print(f'No FCM token for {user.full_name}: {e}')
    return None


def send_push_to_multiple(
        tokens: list,
        title: str,
        body: str,
        data: dict = None):
    """Send push to multiple devices at once"""
    _init_firebase()
    if not firebase_admin._apps or not tokens:
        return None
    try:
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data={k: str(v) for k, v in (data or {}).items()},
            tokens=tokens[:500],  # FCM max 500 at once
            android=messaging.AndroidConfig(
                priority='high',
            ),
        )
        response = messaging.send_each_for_multicast(message)
        print(f'Multicast sent: {response.success_count} success, {response.failure_count} failed')
        return response
    except Exception as e:
        print(f'Multicast error: {e}')
        return None


def send_push_to_nearby_workers(
        district: str,
        title: str,
        body: str,
        data: dict = None):
    """Send push to all available verified workers in district"""
    from users.models import WorkerProfile
    from notifications.models import FCMToken

    workers = WorkerProfile.objects.filter(
        user__district=district,
        is_available=True,
        verification_status='verified',
    ).select_related('user')

    tokens = []
    for worker in workers:
        try:
            fcm = worker.user.fcm_token
            if fcm and fcm.token:
                tokens.append(fcm.token)
        except Exception:
            pass

    if tokens:
        send_push_to_multiple(tokens, title, body, data)
        print(f'Notified {len(tokens)} workers in {district}')


def send_push_to_all_workers(
        title: str,
        body: str,
        data: dict = None):
    """Send push to ALL available verified workers"""
    from users.models import WorkerProfile

    workers = WorkerProfile.objects.filter(
        is_available=True,
        verification_status='verified',
    ).select_related('user')

    tokens = []
    for worker in workers:
        try:
            fcm = worker.user.fcm_token
            if fcm and fcm.token:
                tokens.append(fcm.token)
        except Exception:
            pass

    if tokens:
        send_push_to_multiple(tokens, title, body, data)