import os
import sys


from .base import *


ALLOWED_HOSTS = ['local.viggio.com.br', 'local.viggio', '127.0.0.1', '0.0.0.0']

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

STATIC_URL = '/staticfiles/'

STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'staticfiles')

MEDIA_URL = '/mediafiles/'

MEDIA_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'mediafiles')

MEDIA_DIRECTORY = 'media'


# Banco de Teste
class DisableMigrations(object):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


if 'test' in sys.argv:

    MIGRATION_MODULES = DisableMigrations()

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'test_sqlite.db',
        }
    }
