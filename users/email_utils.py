from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
import random
import string


def generate_code():
    return ''.join(random.choices(string.digits, k=6))


def send_verification_email(user, code, token):
    """Send beautiful HTML verification email"""
    verification_link = (
        f"{settings.FRONTEND_URL}/verify-email?token={token}"
    )

    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Helvetica Neue', Arial, sans-serif;
                background-color: #f8f9fa;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background: white;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            }}
            .header {{
                background: linear-gradient(135deg, #00A651, #007A3D);
                padding: 40px 30px;
                text-align: center;
            }}
            .logo {{
                width: 80px;
                height: 80px;
                background: white;
                border-radius: 20px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 16px;
            }}
            .logo-text {{
                font-size: 32px;
                font-weight: bold;
                color: #00A651;
                line-height: 80px;
            }}
            .app-name {{
                color: white;
                font-size: 28px;
                font-weight: bold;
                margin: 0;
            }}
            .tagline {{
                color: rgba(255,255,255,0.8);
                font-size: 14px;
                margin-top: 6px;
            }}
            .body {{
                padding: 40px 30px;
            }}
            .greeting {{
                font-size: 22px;
                font-weight: bold;
                color: #1a1a2e;
                margin-bottom: 12px;
            }}
            .message {{
                color: #666;
                font-size: 15px;
                line-height: 1.7;
                margin-bottom: 32px;
            }}
            .code-box {{
                background: #f0fdf4;
                border: 2px dashed #00A651;
                border-radius: 16px;
                padding: 24px;
                text-align: center;
                margin-bottom: 28px;
            }}
            .code-label {{
                color: #666;
                font-size: 13px;
                margin-bottom: 10px;
            }}
            .code {{
                font-size: 42px;
                font-weight: bold;
                color: #00A651;
                letter-spacing: 10px;
            }}
            .code-expiry {{
                color: #999;
                font-size: 12px;
                margin-top: 10px;
            }}
            .divider {{
                text-align: center;
                color: #999;
                margin: 24px 0;
                font-size: 14px;
            }}
            .btn {{
                display: block;
                background: linear-gradient(135deg, #00A651, #007A3D);
                color: white;
                text-decoration: none;
                padding: 16px 32px;
                border-radius: 14px;
                font-size: 16px;
                font-weight: bold;
                text-align: center;
                margin-bottom: 28px;
            }}
            .warning {{
                background: #fff8e1;
                border-left: 4px solid #ffd600;
                padding: 14px 16px;
                border-radius: 8px;
                font-size: 13px;
                color: #666;
                margin-bottom: 24px;
            }}
            .footer {{
                background: #f8f9fa;
                padding: 24px 30px;
                text-align: center;
                color: #999;
                font-size: 12px;
                border-top: 1px solid #eee;
            }}
            .footer a {{
                color: #00A651;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Header -->
            <div class="header">
                <div class="logo">
                    <span class="logo-text">JL</span>
                </div>
                <h1 class="app-name">JobLink</h1>
                <p class="tagline">Find skilled workers near you</p>
            </div>

            <!-- Body -->
            <div class="body">
                <p class="greeting">
                    Hello {user.full_name.split()[0]}! 👋
                </p>
                <p class="message">
                    Welcome to JobLink! We're excited to have you on board.
                    To complete your registration and start using the app,
                    please verify your email address.
                </p>

                <!-- Code Box -->
                <div class="code-box">
                    <p class="code-label">Your verification code</p>
                    <p class="code">{code}</p>
                    <p class="code-expiry">⏰ Expires in 10 minutes</p>
                </div>

                <div class="divider">— or click the button below —</div>

                <!-- Verify Button -->
                <a href="{verification_link}" class="btn">
                    ✅ Verify My Email Address
                </a>

                <!-- Warning -->
                <div class="warning">
                    🔒 If you didn't create a JobLink account,
                    please ignore this email. Your email will
                    not be added without verification.
                </div>

                <p style="color: #999; font-size: 13px;">
                    If the button doesn't work, copy and paste
                    this link in your browser:<br>
                    <a href="{verification_link}"
                       style="color: #00A651; word-break: break-all;">
                        {verification_link}
                    </a>
                </p>
            </div>

            <!-- Footer -->
            <div class="footer">
                <p>© 2026 JobLink Rwanda. All rights reserved.</p>
                <p>
                    <a href="#">Privacy Policy</a> ·
                    <a href="#">Terms of Service</a> ·
                    <a href="#">Help Center</a>
                </p>
                <p style="margin-top: 12px; color: #bbb;">
                    You received this email because you registered
                    on JobLink. This is an automated message,
                    please do not reply.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    plain_message = f"""
Hello {user.full_name},

Welcome to JobLink!

Your verification code is: {code}

Or click this link to verify your email:
{verification_link}

This code expires in 10 minutes.

If you didn't create a JobLink account, please ignore this email.

© 2026 JobLink Rwanda
    """

    try:
        send_mail(
            subject='✅ Verify your JobLink email address',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email send error: {e}")
        return False


def send_welcome_email(user):
    """Send welcome email after verification"""
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background: #f8f9fa; }}
            .container {{
                max-width: 600px; margin: 40px auto;
                background: white; border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            }}
            .header {{
                background: linear-gradient(135deg, #00A651, #007A3D);
                padding: 40px; text-align: center;
            }}
            .body {{ padding: 40px; }}
            .btn {{
                display: block; background: #00A651;
                color: white; text-decoration: none;
                padding: 16px; border-radius: 14px;
                font-weight: bold; text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="color:white;margin:0">
                    🎉 Welcome to JobLink!
                </h1>
            </div>
            <div class="body">
                <h2>Hi {user.full_name.split()[0]}!</h2>
                <p style="color:#666;line-height:1.7">
                    Your email has been verified successfully.
                    Your JobLink account is now active!
                </p>
                <p style="color:#666;line-height:1.7">
                    {"As a <b>worker</b>, you can now browse jobs, apply, and start earning." if user.role == "worker" else "As a <b>client</b>, you can now post jobs and find skilled workers near you."}
                </p>
                <br>
                <a href="#" class="btn">
                    Open JobLink App
                </a>
                <br>
                <p style="color:#999;font-size:13px;text-align:center">
                    © 2026 JobLink Rwanda
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    send_mail(
        subject='🎉 Welcome to JobLink — Account Activated!',
        message=f'Welcome to JobLink, {user.full_name}! Your account is now active.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=True,
    )