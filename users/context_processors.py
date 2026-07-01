from django.conf import settings


def oauth_settings(request):
    return {
        'GOOGLE_CLIENT_ID': settings.GOOGLE_CLIENT_ID,
        'FACEBOOK_APP_ID': settings.FACEBOOK_APP_ID,
    }
