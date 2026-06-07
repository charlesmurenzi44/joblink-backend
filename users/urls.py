from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .reviews_views import UserReviewsView
from .views import (
    RegisterView, LoginView, ProfileView,
    WorkerProfileView, PortfolioUploadView,
    SavedWorkerView, MyReviewsView,
    UploadProfilePhotoView,
    UploadPortfolioPhotoView,
    DeletePortfolioPhotoView,
    SendOTPView, VerifyOTPView,
    SubmitVerificationView,
    VerificationStatusView,
    AdminVerificationListView,
    AdminReviewVerificationView,
    VerifyEmailCodeView,
    VerifyEmailTokenView,
    ResendVerificationEmailView,
    RequestPasswordResetView,
    ConfirmPasswordResetView,
)

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('profile/', ProfileView.as_view()),
    path('profile/photo/', UploadProfilePhotoView.as_view()),
    path('worker/profile/', WorkerProfileView.as_view()),
    path('worker/portfolio/', PortfolioUploadView.as_view()),
    path('worker/portfolio/upload/', UploadPortfolioPhotoView.as_view()),
    path('worker/portfolio/<int:pk>/delete/', DeletePortfolioPhotoView.as_view()),
    path('saved-workers/', SavedWorkerView.as_view()),
    path('my-reviews/', MyReviewsView.as_view()),
    path('<int:user_id>/reviews/', UserReviewsView.as_view()),
    # Email Verification
    path('verify-email/code/', VerifyEmailCodeView.as_view()),
    path('verify-email/token/<uuid:token>/', VerifyEmailTokenView.as_view()),
    path('verify-email/resend/', ResendVerificationEmailView.as_view()),
    path('password-reset/request/', RequestPasswordResetView.as_view()),
    path('password-reset/confirm/', ConfirmPasswordResetView.as_view()),
    # Phone/ID Verification
    path('verify/send-otp/', SendOTPView.as_view()),
    path('verify/confirm-otp/', VerifyOTPView.as_view()),
    path('verify/submit/', SubmitVerificationView.as_view()),
    path('verify/status/', VerificationStatusView.as_view()),
    # Admin
    path('admin/verifications/', AdminVerificationListView.as_view()),
    path('admin/verifications/<int:pk>/review/', AdminReviewVerificationView.as_view()),
]