import sys
from django.contrib.auth import get_user_model
from django.db import transaction
from sentry_sdk import capture_exception

from orders.models import (
    AgencyProfit as DjangoAgencyProfit,
    Buyer as DjangoBuyer,
    Charge as DjangoCharge,
    CreditCard as DjangoCreditCard,
    TalentProfit as DjangoTalentProfit,
    Order as DjangoOrder,
)
from request_shoutout.domain.messages import (
    ShoutoutUploadedEvent,
    ShoutoutSuccessfullyRequestedEvent,
)
from request_shoutout.domain.ports import DataBaseUnitOfWork, ProcessPaymentUnitOfWork
from shoutouts.models import ShoutoutVideo as DjangoShoutoutVideo
from utils.telegram import send_high_priority_notification
from wirecard.services import (
    CapturePaymentApi,
    OrderApi,
    PaymentApi,
    WirecardOrderApi,
    WirecardPaymentApi,
)
User = get_user_model()


class PersistingShoutoutRequestError(Exception):
    pass


class PersistRequestShoutoutUnitOfWork(DataBaseUnitOfWork):

    def order_repository_add(self, order):
        self._order = order

    def charge_repository_add(self, charge):
        self._charge = charge

    def credit_card_repository_add(self, credit_card):
        self._credit_card = credit_card

    def buyer_repository_add(self, buyer):
        self._buyer = buyer

    def commit(self):
        try:
            with transaction.atomic():
                DjangoOrder.persist(self._order)
                self._charge.order_id = self._order.id
                DjangoCharge.persist(self._charge)
                self._credit_card.charge_id = self._charge.id
                DjangoCreditCard.persist(self._credit_card)
                self._buyer.charge_id = self._charge.id
                DjangoBuyer.persist(self._buyer)
        except Exception:
            capture_exception()
            raise PersistingShoutoutRequestError()


class ChargingShoutoutRequestError(Exception):
    pass


class PaymentProcessUnitOfWork(ProcessPaymentUnitOfWork):

    def __init__(self, bus):
        self.bus = bus
        self.payment_gateway = WirecardOrderApi(OrderApi(), PaymentApi())

    def charge(self, order):
        try:
            wirecard_order = self.payment_gateway.create_order(order)
            wirecard_payment = self.payment_gateway.create_payment(
                order_data=order,
                wirecard_order_hash=wirecard_order.id,
                delay_capture=True,
            )
            self.payment_gateway.persist_transaction_data(
                order=order,
                wirecard_order_hash=wirecard_order.id,
                wirecard_payment_hash=wirecard_payment.id,
            )
        except Exception as e:
            order.charge.set_failed_status()
            capture_exception()
            traceback = sys.exc_info()[2]
            raise ChargingShoutoutRequestError(e).with_traceback(traceback)
        else:
            order.charge.set_processing_status()
            event = ShoutoutSuccessfullyRequestedEvent(order)
            self.bus.handle(event)
        finally:
            DjangoCharge.persist(order.charge)


class PersistingShoutoutVideoError(Exception):
    pass


class FulfillShoutoutRequestUnitOfWork(DataBaseUnitOfWork):

    def __init__(self):
        self._agency_profit = None

    def talent_profit_repository_add(self, talent_profit):
        self._talent_profit = talent_profit

    def agency_profit_repository_add(self, agency_profit):
        self._agency_profit = agency_profit

    def shoutout_repository_add(self, shoutout):
        self._shoutout = shoutout

    def commit(self):
        try:
            with transaction.atomic():
                DjangoShoutoutVideo.persist(self._shoutout)
                DjangoTalentProfit.persist(self._talent_profit)
                if self._agency_profit:
                    DjangoAgencyProfit.persist(self._agency_profit)
        except Exception as e:
            capture_exception()
            traceback = sys.exc_info()[2]
            raise PersistingShoutoutVideoError(e).with_traceback(traceback)


class CapturingPaymentError(Exception):
    pass


class CapturePaymentUnitOfWork:

    def __init__(self, bus):
        self.bus = bus
        self.payment_gateway = WirecardPaymentApi(CapturePaymentApi())

    def capture(self, transaction_data):
        try:
            wirecard_payment_hash = transaction_data.wirecard_payment_hash
            self.payment_gateway.capture_payment(wirecard_payment_hash)
        except Exception as e:
            capture_exception(e)
            message = (
                'OCORREU UM ERRO AO CAPTURAR UM PAGAMENTO. '
                'Verifique o Sentry: '
                'https://sentry.io/organizations/viggio-sandbox/issues/?project=1770932'
            )
            send_high_priority_notification(message)
        event = ShoutoutUploadedEvent(transaction_data.order.hash_id)
        self.bus.handle(event)
