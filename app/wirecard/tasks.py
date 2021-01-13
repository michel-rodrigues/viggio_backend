from sentry_sdk import capture_exception
from dateutil.parser import parse

from project_configuration.celery import app
from orders.models import Charge
from request_shoutout.domain.models import Charge as DomainCharge

from .models import WirecardTransactionData


CROSS_SYSTEMS_STATUS_MAPPING = {
    'WAITING': DomainCharge.PROCESSING,
    'IN_ANALYSIS': DomainCharge.PROCESSING,
    'PRE_AUTHORIZED': DomainCharge.PRE_AUTHORIZED,
    'AUTHORIZED': DomainCharge.PAID,
    'CANCELLED': DomainCharge.CANCELLED,
    'REFUNDED': DomainCharge.CANCELLED,
    'REVERSED': DomainCharge.CANCELLED,
    'SETTLED': DomainCharge.PAID,
}


def _update_status(wirecard_status, wirecard_payment_hash):
    (
        Charge.objects
        .filter(order__third_party_transaction__wirecard_payment_hash=wirecard_payment_hash)
        .update(status=CROSS_SYSTEMS_STATUS_MAPPING[wirecard_status])
    )


def _update_payment_event_timestamp(wirecard_transaction, payment_event_timestamp):
    wirecard_transaction.payment_event_last_timestamp = payment_event_timestamp
    wirecard_transaction.save()


def _is_a_delayied_notification(payment_event_timestamp, wirecard_transaction):
    if wirecard_transaction.payment_event_last_timestamp:
        return payment_event_timestamp < wirecard_transaction.payment_event_last_timestamp
    return False


@app.task
def update_payment_status(notification):
    payment_event_timestamp = parse(notification['resource']['payment']['updatedAt'])
    payment_status = notification['resource']['payment']['status']
    wirecard_payment_hash = notification['resource']['payment']['id']
    try:
        wirecard_transaction = (
            WirecardTransactionData.objects.get(wirecard_payment_hash=wirecard_payment_hash)
        )
    # Algumas vezes tem subido essa exceção, como não sabemos se é devido à falhas na sandbox
    # da wirecard, estamos evitando quebrar a aplicação e enviando a exceção para o sentry
    except WirecardTransactionData.DoesNotExist:
        capture_exception()
    else:
        if not _is_a_delayied_notification(payment_event_timestamp, wirecard_transaction):
            _update_status(payment_status, wirecard_payment_hash)
            _update_payment_event_timestamp(wirecard_transaction, payment_event_timestamp)
