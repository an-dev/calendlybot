from .staging import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True

DEBUG = False
SITE_URL = 'https://www.calenduck.co'
GTAG_ID = 'UA-158067941-1'

SENTRY_KEY = '6b7be15082fd4466a6df0d0f9d1a12d7'
SENTRY_PROJECT = '5201100'

sentry_sdk.init(
    dsn=f"https://{SENTRY_KEY}@o378137.ingest.sentry.io/{SENTRY_PROJECT}",
    integrations=[DjangoIntegration()],

    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True
)

CELERY_EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp-relay.sendinblue.com'
EMAIL_PORT = 587

EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
