from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    CustomTokenObtainPairSerializer,
    EmailOTPRequestSerializer,
    EmailOTPVerifySerializer,
    PhoneOTPRequestSerializer,
    PhoneOTPVerifySerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    GoogleAuthSerializer,
    FacebookAuthSerializer,
    get_tokens_for_user,
)

User = get_user_model()


# ── Standard Auth ──────────────────────────────────────────────────────────

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        return Response({
            'message': 'Account created! Please verify your email with the OTP sent.',
            'user': UserSerializer(user).data,
            **tokens,
        }, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        refresh = request.data.get('refresh')
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except TokenError:
                pass
        return Response(
            {'message': 'Logged out successfully.'},
            status=status.HTTP_200_OK,
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (request.user.role == 'admin' or request.user.is_superuser)
        )


class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser,)

    def get_queryset(self):
        queryset = User.objects.all()
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        return queryset


# ── Social Auth ────────────────────────────────────────────────────────────

class GoogleLoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        return Response({
            'message': 'Logged in with Google successfully.',
            'user': UserSerializer(user).data,
            **tokens,
        }, status=status.HTTP_200_OK)


class FacebookLoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = FacebookAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        return Response({
            'message': 'Logged in with Facebook successfully.',
            'user': UserSerializer(user).data,
            **tokens,
        }, status=status.HTTP_200_OK)


# ── Email OTP ──────────────────────────────────────────────────────────────

class EmailOTPRequestView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = EmailOTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'message': 'Verification OTP sent to your email address.'},
            status=status.HTTP_200_OK,
        )


class EmailOTPVerifyView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = EmailOTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            'message': 'Email verified successfully.',
            'user': UserSerializer(user).data,
        }, status=status.HTTP_200_OK)


# ── Phone OTP ──────────────────────────────────────────────────────────────

class PhoneOTPRequestView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = PhoneOTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(
            {'message': 'Verification OTP sent to your phone number.'},
            status=status.HTTP_200_OK,
        )


class PhoneOTPVerifyView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = PhoneOTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            'message': 'Phone number verified successfully.',
            'user': UserSerializer(user).data,
        }, status=status.HTTP_200_OK)


# ── Password Reset ─────────────────────────────────────────────────────────

class PasswordResetRequestView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'message': 'If that email address is registered, you will receive a password reset link.'},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'message': 'Password reset successfully. You can now login with your new password.'},
            status=status.HTTP_200_OK,
        )
