from datetime import datetime, timezone

from request_shoutout.domain import emails
from request_shoutout.domain.emails.templates import MailRequest
from request_shoutout.domain.emails.template_builders import (
    customer_order_detail_template_builder,
    notify_talent_about_new_order_template_builder,
)
from request_shoutout.domain.models import Buyer, Charge, CreditCard, Order


def persist_request_shoutout(command, unit_of_work):
    credit_card = CreditCard(
        fullname=command.credit_card_owner_fullname,
        birthdate=command.credit_card_owner_birthdate,
        tax_document=command.credit_card_owner_tax_document,
        phone_number=command.credit_card_owner_phone_number,
        area_code=command.credit_card_owner_area_code,
        credit_card_hash=command.credit_card_hash,
    )
    buyer = Buyer(
        fullname=command.customer_fullname,
        birthdate=command.customer_birthdate,
        tax_document=command.customer_tax_document,
        phone_number=command.customer_phone_number,
        area_code=command.customer_area_code,
    )
    charge = Charge(
        amount_paid=command.order_amount_paid,
        status=Charge.NOT_PROCESSED,
        payment_date=datetime.now(timezone.utc),
        funding_instrument=credit_card,
        buyer=buyer,
    )
    order = Order(
        hash_id=command.order_hash_id,
        talent_id=command.order_talent_id,
        video_is_for=command.order_video_is_for,
        is_from=command.order_is_from,
        is_to=command.order_is_to,
        instruction=command.order_instruction,
        email=command.order_email,
        is_public=command.order_is_public,
        charge=charge,
    )
    unit_of_work.order_repository_add(order)
    unit_of_work.charge_repository_add(charge)
    unit_of_work.credit_card_repository_add(credit_card)
    unit_of_work.buyer_repository_add(buyer)
    unit_of_work.commit()


def process_payment(command, unit_of_work, view_order):
    order = view_order(command.order_hash_id)
    unit_of_work.charge(order)


def send_info_to_customer_about_his_shoutout_request(event, mail_sender, view_talent):
    talent = view_talent(event.order.talent_id)
    to_customer = MailRequest(
        from_email=emails.CONTACT_EMAIL,
        to_email=f'{event.order.is_from} <{event.order.email}>',
        template=customer_order_detail_template_builder(event.order, talent),
    )
    mail_sender.send(to_customer)


def notify_talent_about_new_shoutout_request(event, mail_sender, view_talent):
    talent = view_talent(event.order.talent_id)
    to_talent = MailRequest(
        from_email=emails.CONTACT_EMAIL,
        to_email=f'{talent.user.get_full_name()} <{talent.user.email}>',
        template=notify_talent_about_new_order_template_builder(event.order, talent),
    )
    mail_sender.send(to_talent)
