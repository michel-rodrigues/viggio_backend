from collections import namedtuple

from request_shoutout.domain.ports import DataBaseUnitOfWork, ProcessPaymentUnitOfWork


class RequestShoutoutFakeUnitOfWork(DataBaseUnitOfWork):

    def order_repository_add(self, order):
        self.order = order

    def charge_repository_add(self, charge):
        self.charge = charge

    def credit_card_repository_add(self, credit_card):
        self.credit_card = credit_card

    def buyer_repository_add(self, buyer):
        self.buyer = buyer

    def commit(self):
        self.was_committed = True


class PaymentProcessFakeUnitOfWork(ProcessPaymentUnitOfWork):

    def charge(self, order):
        order.charge.set_processing_status()
        if order.charge.amount_paid > 10000:
            order.charge.set_failed_status()


class FulfillShoutoutRequestFakeUnitOfWork(DataBaseUnitOfWork):

    def talent_profit_repository_add(self, talent_profit):
        self.talent_profit = talent_profit

    def agency_profit_repository_add(self, agency_profit):
        self.agency_profit = agency_profit

    def shoutout_repository_add(self, shoutout):
        self.shoutout = shoutout

    def commit(self):
        self.was_committed = True


SentMail = namedtuple('fake_sent_mail', 'from_email to_email template_name subject data')


def fake_sender(sent):

    def send(mail_request):
        sent_mail = SentMail(
            mail_request.from_email,
            mail_request.to_email,
            mail_request.template.name,
            mail_request.template.subject,
            mail_request.template.data,
        )
        sent.append(sent_mail)

    return send
