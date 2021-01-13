import os


CONTACT_EMAIL = os.environ['CONTACT_EMAIL']

STAFF_EMAIL = os.environ['STAFF_EMAIL']


class EmailSender:

    def __init__(self, mail_carrier):
        self._mail_carrier = mail_carrier

    def send(self, mail_request):
        self._mail_carrier(mail_request)
