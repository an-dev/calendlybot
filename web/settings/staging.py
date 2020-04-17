import django_heroku
from .base import *


MIDDLEWARE.append('whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

SITE_URL = 'https://calendlybot.herokuapp.com'


django_heroku.settings(locals())

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
        "require_debug_true": {"()": "django.utils.log.RequireDebugTrue"},
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
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
        "django.server": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "django.server",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO"},
        "django.server": {"handlers": ["django.server"], "level": "INFO", "propagate": False},
        "web": {"handlers": ["console"], "level": "INFO", "propagate": True},
        "celery": {"handlers": ["console"], "level": "INFO", "propagate": True},
        "celery.redirected": {"handlers": ["console"], "level": "DEBUG", "propagate": True},
    },
}

CELERY_BROKER_URL = os.environ["CLOUDAMQP_URL"]
