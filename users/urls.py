from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    CustomTokenObtainPairView,
    LogoutView,
    UserProfileView,
    UserListView,
    GoogleLoginView,
    FacebookLoginView,
    EmailOTPRequestView,
    EmailOTPVerifyView,
    PhoneOTPRequestView,
    PhoneOTPVerifyView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)

urlpatterns = [
    # Standard auth
    path('register/',      RegisterView.as_view(),              name='auth_register'),
    path('login/',         CustomTokenObtainPairView.as_view(), name='auth_login'),
    path('logout/',        LogoutView.as_view(),                name='auth_logout'),
    path('token/refresh/', TokenRefreshView.as_view(),          name='token_refresh'),
    path('profile/',       UserProfileView.as_view(),           name='user_profile'),
    path('',               UserListView.as_view(),              name='user_list'),

    # Social auth
    path('auth/google/',   GoogleLoginView.as_view(),   name='auth_google'),
    path('auth/facebook/', FacebookLoginView.as_view(), name='auth_facebook'),

    # Email OTP
    path('otp/email/send/',   EmailOTPRequestView.as_view(), name='otp_email_send'),
    path('otp/email/verify/', EmailOTPVerifyView.as_view(),  name='otp_email_verify'),

    # Phone OTP
    path('otp/phone/send/',   PhoneOTPRequestView.as_view(), name='otp_phone_send'),
    path('otp/phone/verify/', PhoneOTPVerifyView.as_view(),  name='otp_phone_verify'),

    # Password reset
    path('password/reset/',         PasswordResetRequestView.as_view(), name='password_reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]
