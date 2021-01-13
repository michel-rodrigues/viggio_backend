from functools import partial

from post_office.mailgun import async_mailgun_carrier
from request_shoutout.adapters.db.orm import (
    CapturePaymentUnitOfWork,
    FulfillShoutoutRequestUnitOfWork,
    PaymentProcessUnitOfWork,
    PersistRequestShoutoutUnitOfWork,
)
from request_shoutout.adapters.db.db_views import (
    view_agency_profit_percentage,
    view_default_talent_profit_percentage,
    view_customized_talent_profit_percentage,
    view_order,
    view_talent,
    view_transaction_data,
)
from request_shoutout.domain.emails.sender import EmailSender
from request_shoutout.domain.factories import AgencyProfitFactory, TalentProfitFactory
from request_shoutout.domain.messages import (
    FulfillShoutoutRequestCommand,
    RequestShoutoutCommand,
    ShoutoutUploadedEvent,
    ShoutoutSuccessfullyRequestedEvent,
    ShoutoutSuccessfullyTranscodedEvent,
)
from request_shoutout.services.request_shoutout import (
    persist_request_shoutout,
    process_payment,
    send_info_to_customer_about_his_shoutout_request,
    notify_talent_about_new_shoutout_request,
)
from request_shoutout.services.fulfill_shoutout_request import (
    capture_payment,
    fulfill_shoutout_request,
    notify_customer_about_shoutout_request_fulfilled,
    schedule_uploaded_shoutout_transcoding,
    validate_order_can_be_fulfilled,
)
from transcoder.tasks import to_mp4
from .garage import MessageBus


# Request Shoutout and Payment Process
def get_charge_order_bus():
    bus = MessageBus()

    # Step 1: Create an Order, Charge and CreditCard
    bus.register(
        RequestShoutoutCommand,
        partial(
            persist_request_shoutout,
            **{'unit_of_work': PersistRequestShoutoutUnitOfWork()}
        ),
    )

    # Step 2: Send payment data to be processed by third party payment gateway
    # and create a WirecardTransctionData
    bus.register(
        RequestShoutoutCommand,
        partial(
            process_payment,
            **{
                'unit_of_work': PaymentProcessUnitOfWork(bus),
                'view_order': view_order,
            }
        ),
    )

    # Step 3: Send an email with info about the shoutout request
    bus.register(
        ShoutoutSuccessfullyRequestedEvent,
        partial(
            send_info_to_customer_about_his_shoutout_request,
            **{
                'mail_sender': EmailSender(async_mailgun_carrier),
                'view_talent': view_talent,
            }
        ),
    )

    # Step 4: Send email to notify talent about a new shoutout request for him
    bus.register(
        ShoutoutSuccessfullyRequestedEvent,
        partial(
            notify_talent_about_new_shoutout_request,
            **{
                'mail_sender': EmailSender(async_mailgun_carrier),
                'view_talent': view_talent,
            }
        ),
    )
    return bus


# Fullfil Shoutout Request
def get_fulfill_shoutout_request_bus():
    bus = MessageBus()

    # Step 1: Validate order
    bus.register(
        FulfillShoutoutRequestCommand,
        partial(
            validate_order_can_be_fulfilled,
            **{'view_order': view_order}
        ),
    )

    # Step 2: create a ShoutoutVideo and a TalentProfit
    bus.register(
        FulfillShoutoutRequestCommand,
        partial(
            fulfill_shoutout_request,
            **{
                'unit_of_work': FulfillShoutoutRequestUnitOfWork(),
                'view_order': view_order,
                'view_talent': view_talent,
                'talent_profit_factory': TalentProfitFactory(
                    view_customized_talent_profit_percentage,
                    view_default_talent_profit_percentage,
                ),
                'agency_profit_factory': AgencyProfitFactory(view_agency_profit_percentage),
            }
        ),
    )

    # Step 3: Request third party payment processor to capture payment
    bus.register(
        FulfillShoutoutRequestCommand,
        partial(
            capture_payment,
            **{
                'unit_of_work': CapturePaymentUnitOfWork(bus),
                'view_transaction_data': view_transaction_data,
            }
        ),
    )

    # At this point, the third party payment processor should have sent a notification
    # and the webhook has updated the charge status

    # Step 4: Transcode to MP4 a ShoutoutVideo
    bus.register(
        ShoutoutUploadedEvent,
        partial(
            schedule_uploaded_shoutout_transcoding,
            **{
                'transcoder': to_mp4,
                'view_order': view_order,
            }
        ),
    )

    # Step 5: Notify customer about his shoutout request was fulfilled
    bus.register(
        ShoutoutSuccessfullyTranscodedEvent,
        partial(
            notify_customer_about_shoutout_request_fulfilled,
            **{
                'mail_sender': EmailSender(async_mailgun_carrier),
                'view_order': view_order,
                'view_talent': view_talent,
            }
        ),
    )
    return bus
