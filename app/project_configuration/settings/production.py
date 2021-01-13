import os

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *


ALLOWED_HOSTS = ['viggio.com.br']

# Disable browseble API
REST_FRAMEWORK.update({
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    )
})

# default file storage for both static and media
DEFAULT_FILE_STORAGE = 'project_configuration.storage_backends.GoogleCloudMediaStorage'
STATICFILES_STORAGE = 'project_configuration.storage_backends.GoogleCloudStaticStorage'

GS_FILE_STORAGE_NAME = os.environ['STORAGE_NAME']
MEDIA_DIRECTORY = os.environ['MEDIA_DIRECTORY']
STATIC_DIRECTORY = os.environ['STATIC_DIRECTORY']

# define the static urls for both static and media
STATIC_URL = os.environ['STORAGE_URL']
MEDIA_URL = os.environ['STORAGE_URL']

sentry_sdk.init(dsn=os.environ.get('SENTRY_DSN'), integrations=[DjangoIntegration()])
