from numbers import Number

from orders.models import (
    CustomTalentProfitPercentage,
    DefaultTalentProfitPercentage,
)
from orders.models import (
    AgencyProfitPercentage as DjangoAgencyProfitPercentage,
    Order as DjangoOrder,
)
from request_shoutout.domain.models import Buyer, Charge, CreditCard, Order, Shoutout
from request_shoutout.domain.models import AgencyProfitPercentage, TalentProfitPercentage
from talents.models import Talent
from wirecard.models import WirecardTransactionData


def view_order(unique_identifier):
    if isinstance(unique_identifier, Number):
        django_orders_queryset = DjangoOrder.objects.filter(id=unique_identifier)
    else:
        django_orders_queryset = DjangoOrder.objects.filter(hash_id=unique_identifier)
    django_orders_queryset = django_orders_queryset.prefetch_related(
        'charge',
        'charge__funding_instrument',
        'charge__buyer',
        'shoutout',
    )
    django_order = django_orders_queryset.first()

    credit_card = CreditCard(
        fullname=django_order.charge.funding_instrument.fullname,
        birthdate=django_order.charge.funding_instrument.birthdate,
        tax_document=django_order.charge.funding_instrument.tax_document,
        credit_card_hash=django_order.charge.funding_instrument.credit_card_hash,
        phone_number=django_order.charge.funding_instrument.phone_number,
        area_code=django_order.charge.funding_instrument.area_code,
    )
    buyer = Buyer(
        fullname=django_order.charge.buyer.fullname,
        birthdate=django_order.charge.buyer.birthdate,
        tax_document=django_order.charge.buyer.tax_document,
        phone_number=django_order.charge.buyer.phone_number,
        area_code=django_order.charge.buyer.area_code,
    )
    charge = Charge(
        order_id=django_order.id,
        amount_paid=django_order.charge.amount_paid,
        payment_date=django_order.charge.payment_date,
        status=django_order.charge.amount_paid,
        payment_method=django_order.charge.payment_method,
        funding_instrument=credit_card,
        buyer=buyer,
    )
    order = Order(
        id=django_order.id,
        hash_id=django_order.hash_id,
        talent_id=django_order.talent_id,
        video_is_for=django_order.video_is_for,
        is_from=django_order.is_from,
        is_to=django_order.is_to,
        instruction=django_order.instruction,
        email=django_order.email,
        is_public=django_order.is_public,
        charge=charge,
    )
    order.created_at = django_order.created_at  # TODO: saporra não deveria estar aqui pq não tem na domain model
    order.expiration_datetime = django_order.expiration_datetime
    if hasattr(django_order, 'shoutout'):
        order.shoutout = Shoutout(
            hash_id=django_order.shoutout.hash_id,
            order_id=django_order.shoutout.order_id,
            talent_id=django_order.shoutout.talent_id,
            video_file=django_order.shoutout.file,
        )
    return order


def view_transaction_data(order_hash):
    # TODO: Criar domain_model TransactionData para retornar nesse db_view???
    return WirecardTransactionData.objects.get(order__hash_id=order_hash)


def view_talent(talent_id):
    # TODO: Criar domain_model Talent para retornar nesse db_view
    return Talent.objects.get(id=talent_id)


def view_customized_talent_profit_percentage(talent_id):
    try:
        profit_percentage = CustomTalentProfitPercentage.objects.get(talent_id=talent_id)
    except CustomTalentProfitPercentage.DoesNotExist:
        profit_percentage = None
    else:
        profit_percentage = TalentProfitPercentage(
            talent_id=profit_percentage.talent_id,
            value=profit_percentage.value,
        )
    return profit_percentage


def view_default_talent_profit_percentage():
    profit_percentage = DefaultTalentProfitPercentage.objects.first()
    domain_profit_percentage = TalentProfitPercentage(
        talent_id=None,
        value=profit_percentage.value,
    )
    return domain_profit_percentage


def view_agency_profit_percentage(agency_id):
    profit_percentage = DjangoAgencyProfitPercentage.objects.get(id=agency_id)
    domain_profit_percentage = AgencyProfitPercentage(
        agency_id=agency_id,
        value=profit_percentage.value,
    )
    return domain_profit_percentage
