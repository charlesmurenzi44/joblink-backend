import logging

from django.conf import settings
from django.core.mail import send_mail

import random
import string

logger = logging.getLogger(__name__)


def generate_code():
    return ''.join(random.choices(string.digits, k=6))


def email_configured() -> bool:
    return bool(getattr(settings, 'EMAIL_CONFIGURED', False))


def send_verification_email(user, code, token):
    """Send HTML verification email. Returns (success, error_message)."""
    if not email_configured():
        logger.info(
            'Email not configured — verification code for %s: %s',
            user.email,
            code,
        )
        print(f"\n{'=' * 40}\nVERIFY EMAIL for {user.email}: {code}\n{'=' * 40}\n")
        return False, 'Email not configured'

    verification_link = (
        f"{settings.FRONTEND_URL}/verify-email?token={token}"
    )

    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family:Arial,sans-serif;background:#f8f9fa;margin:0;padding:24px">
      <div style="max-width:560px;margin:0 auto;background:#fff;border-radius:16px;padding:32px">
        <h1 style="color:#00A651;margin:0 0 8px">JobLink</h1>
        <p style="color:#666">Hello {user.full_name.split()[0]},</p>
        <p style="color:#666;line-height:1.6">
          Your verification code is below. It expires in 10 minutes.
        </p>
        <p style="font-size:36px;font-weight:bold;color:#00A651;letter-spacing:8px;text-align:center">
          {code}
        </p>
        <p style="text-align:center;margin:24px 0">
          <a href="{verification_link}" style="background:#00A651;color:#fff;padding:14px 24px;
             border-radius:12px;text-decoration:none;font-weight:bold">
            Verify email
          </a>
        </p>
        <p style="color:#999;font-size:12px">
          If you did not register, ignore this email.
        </p>
      </div>
    </body>
    </html>
    """

    plain_message = (
        f'Hello {user.full_name},\n\n'
        f'Your JobLink verification code is: {code}\n\n'
        f'Or verify here: {verification_link}\n\n'
        f'This code expires in 10 minutes.\n'
    )

    try:
        send_mail(
            subject='Verify your JobLink email',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info('Verification email sent to %s', user.email)
        return True, ''
    except Exception as exc:
        logger.exception('Verification email failed for %s', user.email)
        return False, str(exc)


def send_password_reset_email(user, code, token):
    """Send password reset email. Returns (success, error_message)."""
    if not email_configured():
        print(f"\n{'=' * 40}\nRESET PASSWORD for {user.email}: {code}\n{'=' * 40}\n")
        return False, 'Email not configured'

    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}&email={user.email}"
    plain = (
        f'Hello {user.full_name},\n\n'
        f'Your JobLink password reset code is: {code}\n\n'
        f'Or reset here: {reset_link}\n\n'
        f'Expires in 15 minutes.\n'
    )
    html = f"""
    <html><body style="font-family:Arial,sans-serif">
      <h2 style="color:#00A651">Reset your password</h2>
      <p>Hello {user.full_name.split()[0]},</p>
      <p style="font-size:32px;font-weight:bold;color:#00A651;letter-spacing:6px">{code}</p>
      <p><a href="{reset_link}" style="background:#00A651;color:#fff;padding:12px 20px;
         border-radius:8px;text-decoration:none">Reset password</a></p>
    </body></html>
    """
    try:
        send_mail(
            subject='Reset your JobLink password',
            message=plain,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html,
            fail_silently=False,
        )
        return True, ''
    except Exception as exc:
        logger.exception('Password reset email failed for %s', user.email)
        return False, str(exc)


def send_welcome_email(user):
    """Send welcome email after verification."""
    if not email_configured():
        return False, 'Email not configured'

    html_message = f"""
    <html><body style="font-family:Arial,sans-serif">
      <h2 style="color:#00A651">Welcome to JobLink, {user.full_name.split()[0]}!</h2>
      <p>Your email is verified and your account is active.</p>
    </body></html>
    """

    try:
        send_mail(
            subject='Welcome to JobLink',
            message=f'Welcome to JobLink, {user.full_name}! Your account is now active.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True, ''
    except Exception as exc:
        logger.exception('Welcome email failed for %s', user.email)
        return False, str(exc)
