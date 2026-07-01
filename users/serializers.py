import secrets
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


# ── Helpers ────────────────────────────────────────────────────────────────

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


# ── Basic ──────────────────────────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'role', 'phone_number',
            'first_name', 'last_name',
            'is_email_verified', 'is_phone_verified', 'social_provider',
        )
        read_only_fields = ('id',)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'role',
                  'phone_number', 'first_name', 'last_name')
        extra_kwargs = {'email': {'required': True}}

    def create(self, validated_data):
        validated_data['role'] = 'client'
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            role='client',
            phone_number=validated_data.get('phone_number', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        # Send email OTP automatically on registration
        otp = user.set_email_otp()
        _send_email_otp(user.email, otp)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        identifier = attrs.get('username', '')
        if '@' in identifier:
            try:
                user = User.objects.get(email__iexact=identifier)
                attrs['username'] = user.username
            except User.DoesNotExist:
                pass
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data


# ── Email OTP ──────────────────────────────────────────────────────────────

def _send_email_otp(email, otp):
    try:
        send_mail(
            subject='TravelAI – Your Verification Code',
            message=(
                f'Your TravelAI verification code is: {otp}\n\n'
                f'This code expires in 10 minutes.\n'
                f'If you did not request this, please ignore this email.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception:
        if settings.DEBUG:
            print(f'[TravelAI DEV] Email OTP for {email}: {otp}')
        else:
            raise


class EmailOTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            self._user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('No account found with this email address.')
        return value

    def save(self):
        otp = self._user.set_email_otp()
        _send_email_otp(self._user.email, otp)
        return self._user


class EmailOTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp   = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError({'email': 'No account found with this email address.'})

        if not user.is_email_otp_valid(attrs['otp']):
            raise serializers.ValidationError({'otp': 'Invalid or expired OTP.'})

        attrs['user'] = user
        return attrs

    def save(self):
        user = self.validated_data['user']
        user.is_email_verified = True
        user.email_otp = None
        user.email_otp_created_at = None
        user.save(update_fields=['is_email_verified', 'email_otp', 'email_otp_created_at'])
        return user


# ── Phone OTP ──────────────────────────────────────────────────────────────

def _send_phone_otp(phone_number, otp):
    """Send SMS via Twilio. Requires TWILIO_* settings."""
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=f'Your TravelAI verification code is: {otp}. Expires in 10 minutes.',
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number,
        )
    except Exception as e:
        raise serializers.ValidationError({'phone_number': f'Failed to send SMS: {str(e)}'})


class PhoneOTPRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)

    def validate_phone_number(self, value):
        # Attach the phone number to the currently authenticated user
        return value

    def save(self, user):
        user.phone_number = self.validated_data['phone_number']
        user.save(update_fields=['phone_number'])
        otp = user.set_phone_otp()
        _send_phone_otp(user.phone_number, otp)
        return user


class PhoneOTPVerifySerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    otp          = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        try:
            user = User.objects.get(phone_number=attrs['phone_number'])
        except User.DoesNotExist:
            raise serializers.ValidationError({'phone_number': 'No account found with this phone number.'})

        if not user.is_phone_otp_valid(attrs['otp']):
            raise serializers.ValidationError({'otp': 'Invalid or expired OTP.'})

        attrs['user'] = user
        return attrs

    def save(self):
        user = self.validated_data['user']
        user.is_phone_verified = True
        user.phone_otp = None
        user.phone_otp_created_at = None
        user.save(update_fields=['is_phone_verified', 'phone_otp', 'phone_otp_created_at'])
        return user


# ── Password Reset ─────────────────────────────────────────────────────────

def _send_reset_email(email, token, request=None):
    base_url = settings.FRONTEND_BASE_URL if hasattr(settings, 'FRONTEND_BASE_URL') else 'http://127.0.0.1:8000'
    reset_url = f'{base_url}/auth/reset-password/?token={token}'
    try:
        send_mail(
            subject='TravelAI – Password Reset Request',
            message=(
                f'You requested a password reset for your TravelAI account.\n\n'
                f'Click the link below to reset your password (expires in 30 minutes):\n'
                f'{reset_url}\n\n'
                f'If you did not request this, please ignore this email.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception:
        if settings.DEBUG:
            print(f'[TravelAI DEV] Password reset for {email}: {reset_url}')
        else:
            raise


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            self._user = User.objects.get(email=value)
        except User.DoesNotExist:
            # Silently succeed to avoid email enumeration
            self._user = None
        return value

    def save(self):
        if self._user:
            token = secrets.token_urlsafe(32)
            self._user.password_reset_token = token
            self._user.password_reset_token_created_at = timezone.now()
            self._user.save(update_fields=[
                'password_reset_token', 'password_reset_token_created_at'
            ])
            _send_reset_email(self._user.email, token)


class PasswordResetConfirmSerializer(serializers.Serializer):
    token        = serializers.CharField()
    new_password = serializers.CharField(min_length=8, write_only=True)

    def validate(self, attrs):
        try:
            user = User.objects.get(password_reset_token=attrs['token'])
        except User.DoesNotExist:
            raise serializers.ValidationError({'token': 'Invalid or expired reset token.'})

        if not user.is_reset_token_valid(attrs['token']):
            raise serializers.ValidationError({'token': 'Reset token has expired.'})

        attrs['user'] = user
        return attrs

    def save(self):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.password_reset_token = None
        user.password_reset_token_created_at = None
        user.save(update_fields=[
            'password', 'password_reset_token', 'password_reset_token_created_at'
        ])
        return user


# ── Google OAuth ───────────────────────────────────────────────────────────

def _unique_username(base):
    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f'{base}{counter}'
        counter += 1
    return username


def _get_or_create_google_user(google_user_id, email, first_name, last_name):
    user = User.objects.filter(social_id=google_user_id).first()
    if user:
        return user, False

    if email:
        user = User.objects.filter(email__iexact=email).first()
        if user:
            if user.social_provider == 'email' or not user.social_id:
                user.social_id = google_user_id
                user.social_provider = 'google'
                user.is_email_verified = True
                if first_name and not user.first_name:
                    user.first_name = first_name
                if last_name and not user.last_name:
                    user.last_name = last_name
                user.save()
                return user, False
            raise serializers.ValidationError({
                'id_token': 'An account with this email already exists. Please login with email/password.',
            })

    base = (email.split('@')[0] if email else f'google_{google_user_id[-6:]}').replace('.', '_')[:20]
    user = User(
        username=_unique_username(base),
        email=email or '',
        first_name=first_name,
        last_name=last_name,
        social_id=google_user_id,
        social_provider='google',
        is_email_verified=bool(email),
        role='client',
    )
    user.set_unusable_password()
    user.save()
    return user, True


class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField()

    def validate(self, attrs):
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests

        if not settings.GOOGLE_CLIENT_ID:
            raise serializers.ValidationError({'id_token': 'Google login is not configured on the server.'})

        try:
            id_info = google_id_token.verify_oauth2_token(
                attrs['id_token'],
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except ValueError as e:
            raise serializers.ValidationError({'id_token': f'Invalid Google token: {str(e)}'})

        google_user_id = id_info.get('sub')
        email = id_info.get('email', '')
        first_name = id_info.get('given_name', '')
        last_name = id_info.get('family_name', '')

        user, _created = _get_or_create_google_user(
            google_user_id, email, first_name, last_name
        )
        attrs['user'] = user
        return attrs

    def save(self):
        return self.validated_data['user']


# ── Facebook OAuth ─────────────────────────────────────────────────────────

class FacebookAuthSerializer(serializers.Serializer):
    access_token = serializers.CharField()

    def validate(self, attrs):
        import requests as req

        # Verify token with Facebook Graph API
        fb_url = (
            f"https://graph.facebook.com/me"
            f"?fields=id,name,email,first_name,last_name"
            f"&access_token={attrs['access_token']}"
        )
        response = req.get(fb_url, timeout=10)
        if response.status_code != 200:
            raise serializers.ValidationError({'access_token': 'Invalid Facebook access token.'})

        fb_data = response.json()
        if 'error' in fb_data:
            raise serializers.ValidationError({'access_token': fb_data['error'].get('message', 'Facebook auth failed.')})

        fb_user_id = fb_data.get('id')
        email      = fb_data.get('email', '')
        first_name = fb_data.get('first_name', '')
        last_name  = fb_data.get('last_name', '')

        user, created = User.objects.get_or_create(
            social_id=fb_user_id,
            defaults={
                'username':         email.split('@')[0] + f'_f{fb_user_id[-4:]}' if email else f'fb_{fb_user_id}',
                'email':            email,
                'first_name':       first_name,
                'last_name':        last_name,
                'social_provider':  'facebook',
                'is_email_verified': bool(email),
            }
        )

        attrs['user'] = user
        return attrs

    def save(self):
        return self.validated_data['user']
