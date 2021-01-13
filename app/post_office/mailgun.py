import abc
import requests
import os

from project_configuration.celery import app


class MailCarrier(abc.ABC):

    def __init__(self, sender):
        self._sender = sender

    def _build_request_data(self, mail_request):
        template_data = mail_request.template.data
        data = {f'v:{field}': getattr(template_data, field) for field in template_data._fields}
        data.update({
            'from': mail_request.from_email,
            'to': mail_request.to_email,
            'subject': mail_request.template.subject,
            'template': mail_request.template.name,
        })
        return data

    @abc.abstractmethod
    def send(self, mail_request):
        pass


class AsyncMailCarrier(MailCarrier):

    def __init__(self, sender):
        self._sender = sender

    def send(self, mail_request):
        return self._sender.delay(self._build_request_data(mail_request))


class SyncMailCarrier(MailCarrier):

    def __init__(self, sender):
        self._sender = sender

    def send(self, mail_request):
        return self._sender(self._build_request_data(mail_request))


def async_mailgun_carrier(mail_request):
    async_mail_carrier = AsyncMailCarrier(mailgun_send_mail_task)
    async_mail_carrier.send(mail_request)


def sync_mailgun_carrier(mail_request):
    sync_mail_carrier = SyncMailCarrier(mailgun_send_mail_task)
    sync_mail_carrier.send(mail_request)


@app.task
def mailgun_send_mail_task(data):
    requests.post(
        url=os.environ['MAILGUN_API_URL'],
        auth=('api', os.environ['MAILGUN_API_KEY']),
        data=data,
    )


def mailgun_send_mail(data):
    requests.post(
        url=os.environ['MAILGUN_API_URL'],
        auth=('api', os.environ['MAILGUN_API_KEY']),
        data=data,
    )
