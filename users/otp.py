import random
import string
from datetime import timedelta
from django.utils import timezone


def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


def is_otp_valid(otp_obj):
    if not otp_obj:
        return False
    expiry = otp_obj.created_at + timedelta(minutes=10)
    return timezone.now() < expiry