from sentry_sdk import capture_exception

from request_shoutout.domain import emails
from request_shoutout.domain.emails.templates import MailRequest
from request_shoutout.domain.emails.template_builders import (
    notify_customer_about_shoutout_request_fulfilled_template_builder,
)
from request_shoutout.domain.models import Shoutout


def validate_order_can_be_fulfilled(command, view_order):
    order = view_order(command.order_hash)
    try:
        order.validate_if_it_can_be_fulfilled(command)
    except Exception as e:
        capture_exception()
        raise e


def fulfill_shoutout_request(
    command,
    unit_of_work,
    view_order,
    view_talent,
    talent_profit_factory,
    agency_profit_factory,
):
    order = view_order(command.order_hash)
    shoutout = Shoutout(
        hash_id=command.shoutout_hash,
        order_id=order.id,
        talent_id=command.talent_id,
        video_file=command.video_file,
    )
    shoutout.order_hash = command.order_hash
    talent_profit = talent_profit_factory(order)
    talent = view_talent(order.talent_id)
    order.shoutout = shoutout
    unit_of_work.shoutout_repository_add(shoutout)
    unit_of_work.talent_profit_repository_add(talent_profit)
    if talent.agency_id:
        agency_profit = agency_profit_factory(order, talent.agency_id)
        unit_of_work.agency_profit_repository_add(agency_profit)
    unit_of_work.commit()


def capture_payment(command, unit_of_work, view_transaction_data):
    transaction_data = view_transaction_data(command.order_hash)
    unit_of_work.capture(transaction_data)


def schedule_uploaded_shoutout_transcoding(event, transcoder, view_order):
    order = view_order(event.order_hash)
    transcoder(order.shoutout.hash_id)


def notify_customer_about_shoutout_request_fulfilled(event, mail_sender, view_order, view_talent):
    order = view_order(event.order_id)
    talent = view_talent(order.talent_id)
    to_customer = MailRequest(
        to_email=f'{order.is_from} <{order.email}>',
        from_email=emails.CONTACT_EMAIL,
        template=notify_customer_about_shoutout_request_fulfilled_template_builder(
            order,
            talent,
            order.shoutout,
        ),
    )
    mail_sender.send(to_customer)
