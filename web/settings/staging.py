import django_heroku
from .base import *


MIDDLEWARE.append('whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

django_heroku.settings(locals())

SITE_URL = 'https://www.calendlybot.herokuapp.com'
