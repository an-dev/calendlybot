from django.conf import settings as django_settings


def settings(request):
    """
    Return a lazy 'messages' context variable as well as
    'DEFAULT_MESSAGE_LEVELS'.
    """
    return {
        'GTAG_ID': django_settings.GTAG_ID,
        'TRIAL_DAYS': django_settings.TRIAL_DAYS,
    }
