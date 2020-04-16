import django_heroku
from .base import *
import logging

logger = logging.getLogger(__name__)


MIDDLEWARE.append('whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

SITE_URL = 'https://calendlybot.herokuapp.com'


def skip_static_requests(record):
    filtered_record = record.args[0]
    logger.info('===============================')
    logger.info(filtered_record)
    if any(['GET path="/static/' in filtered_record, 'GET /static/' in filtered_record]):  # filter whatever you want
        return False
    return True


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
        "require_debug_true": {"()": "django.utils.log.RequireDebugTrue"},
        # use Django's built in CallbackFilter to point to your filter
        'skip_static_requests': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': skip_static_requests
        }
    },
    "formatters": {
        "django.server": {
            "()": "django.utils.log.ServerFormatter",
            "format": "[%(server_time)s] %(message)s",
        },
        "console": {
            "()": "django.utils.log.ServerFormatter",
            "format": "%(levelname)-8s [%(asctime)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "null": {"level": "DEBUG", "class": "logging.NullHandler"},
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
        "django.server": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "django.server",
            'filters': ['skip_static_requests'],
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "loggers": {
        "django": {"handlers": ["django.server"], "level": "INFO"},
        "django.server": {"handlers": ["django.server"], "level": "INFO", "propagate": False},
        "web": {"handlers": ["console"], "level": "INFO", "propagate": True},
        "celery": {"handlers": ["console"], "level": "INFO", "propagate": True},
        "celery.redirected": {"handlers": ["console"], "level": "DEBUG", "propagate": True},
    },
}

CELERY_BROKER_URL = os.environ["CLOUDAMQP_URL"]

django_heroku.settings(locals())
