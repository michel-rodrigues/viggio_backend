import os
from celery import Celery


ENVIRONMENT = os.environ['ENVIRONMENT']
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'project_configuration.settings.{ENVIRONMENT}')

app = Celery('project_configuration')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
