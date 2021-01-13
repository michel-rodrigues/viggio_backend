import uuid
from collections import namedtuple
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest

from request_shoutout.domain.emails.sender import EmailSender
from request_shoutout.domain.messages import (
    RequestShoutoutCommand,
    ShoutoutSuccessfullyRequestedEvent,
)
from request_shoutout.domain.models import Charge, Order, RequiredFieldError
from request_shoutout.services.request_shoutout import (
    notify_talent_about_new_shoutout_request,
    persist_request_shoutout,
    process_payment,
    send_info_to_customer_about_his_shoutout_request,
)
from request_shoutout.tests.fakes.adapters import (
    fake_sender,
    PaymentProcessFakeUnitOfWork,
    RequestShoutoutFakeUnitOfWork,
)
from request_shoutout.tests.fakes.db_views import FakeDBView


DATA = {
    'order_hash_id': uuid.uuid4(),
    'order_video_is_for': 'someone_else',
    'order_is_from': 'MJ',
    'order_is_to': 'Peter',
    'order_instruction': "Go Get 'em, Tiger",
    'order_email': 'mary.jane.watson@spiderman.com',
    'order_talent_id': 1,
    'order_amount_paid': 150,
    'order_is_public': 'True',
    'customer_fullname': 'Mary Jane Watson',
    'customer_birthdate': '31/12/2019',
    'customer_phone_number': '987654321',
    'customer_area_code': '11',
    'customer_tax_document': '12345678910',
    'credit_card_owner_fullname': 'Pater Parker',
    'credit_card_owner_birthdate': '31/12/2019',
    'credit_card_owner_phone_number': '123465789',
    'credit_card_owner_area_code': '11',
    'credit_card_owner_tax_document': '01234567890',
    'credit_card_hash': '<encrypted-credit-card-hash>',
}


class TestWhenRequestingAShoutout:

    def setup_method(self):
        self.unit_of_work = RequestShoutoutFakeUnitOfWork()
        command = RequestShoutoutCommand(**DATA)
        persist_request_shoutout(command, self.unit_of_work)

    def test_it_should_create_a_new_order(self):
        assert self.unit_of_work.order is not None

    def test_order_should_have_a_hash_id(self):
        assert isinstance(self.unit_of_work.order.hash_id, uuid.UUID)

    def test_it_should_record_data_from_command_to_the_order(self):
        assert self.unit_of_work.order.talent_id == DATA['order_talent_id']
        assert self.unit_of_work.order.video_is_for == DATA['order_video_is_for']
        assert self.unit_of_work.order.is_from == DATA['order_is_from']
        assert self.unit_of_work.order.is_to == DATA['order_is_to']
        assert self.unit_of_work.order.instruction == DATA['order_instruction']
        assert self.unit_of_work.order.email == DATA['order_email']
        assert self.unit_of_work.order.is_public == DATA['order_is_public']

    def test_it_should_set_expiration_datetime_five_days_minus_one_hour_from_now(self):
        five_days_from_today = datetime.now(timezone.utc) + timedelta(days=5)
        five_days_minus_one_hour_from_now = five_days_from_today - timedelta(hours=1)
        expiration_datetime = self.unit_of_work.order.expiration_datetime
        assert expiration_datetime.date() == five_days_minus_one_hour_from_now.date()
        assert expiration_datetime.hour == five_days_minus_one_hour_from_now.hour

    def test_it_should_attach_a_charge_to_order(self):
        assert self.unit_of_work.order.charge is not None

    def test_it_should_set_not_processed_status(self):
        assert self.unit_of_work.charge.status == Charge.NOT_PROCESSED

    def test_charge_should_have_payment_data(self):
        utc_now = datetime.now(timezone.utc)
        assert isinstance(self.unit_of_work.charge.amount_paid, Decimal)
        assert self.unit_of_work.charge.amount_paid == 150
        assert self.unit_of_work.charge.payment_date.date() == utc_now.date()
        assert self.unit_of_work.charge.payment_date.hour == utc_now.hour
        assert self.unit_of_work.charge.payment_date.minute == utc_now.minute
        assert self.unit_of_work.charge.payment_method == 'credit_card'

    def test_charge_should_have_payment_method_object(self):
        funding_instrument = self.unit_of_work.charge.funding_instrument
        assert funding_instrument.fullname == DATA['credit_card_owner_fullname']
        assert funding_instrument.birthdate == DATA['credit_card_owner_birthdate']
        assert funding_instrument.phone_number == DATA['credit_card_owner_phone_number']
        assert funding_instrument.area_code == DATA['credit_card_owner_area_code']
        assert funding_instrument.tax_document == DATA['credit_card_owner_tax_document']
        assert funding_instrument.credit_card_hash == '<encrypted-credit-card-hash>'

    def test_charge_should_have_buyer_object(self):
        assert self.unit_of_work.charge.buyer.fullname == DATA['customer_fullname']
        assert self.unit_of_work.charge.buyer.birthdate == DATA['customer_birthdate']
        assert self.unit_of_work.charge.buyer.phone_number == DATA['customer_phone_number']
        assert self.unit_of_work.charge.buyer.area_code == DATA['customer_area_code']
        assert self.unit_of_work.charge.buyer.tax_document == DATA['customer_tax_document']

    def test_it_should_committ_the_unit_of_work(self):
        assert self.unit_of_work.was_committed is True


class TestWhenRequestingAShoutoutToMyself:

    def setup_method(self):
        self.data = dict(DATA)
        self.data['order_video_is_for'] = 'myself'
        self.data.pop('order_is_from')  # is_from field is not required
        self.unit_of_work = RequestShoutoutFakeUnitOfWork()
        command = RequestShoutoutCommand(**self.data)
        persist_request_shoutout(command, self.unit_of_work)

    def test_is_from_field_should_be_the_same_as_is_to_field(self):
        assert self.unit_of_work.order.video_is_for == self.data['order_video_is_for']
        assert self.unit_of_work.order.is_from == self.data['order_is_to']


class TestWhenRequestingAShoutoutToSomeoneElse:

    def setup_method(self):
        self.data = dict(DATA)
        self.data.pop('order_is_from')
        self.unit_of_work = RequestShoutoutFakeUnitOfWork()
        self.command = RequestShoutoutCommand(**self.data)

    def test_it_should_raise_a_exception_if_missing_is_from_field(self):
        with pytest.raises(RequiredFieldError):
            persist_request_shoutout(self.command, self.unit_of_work)


class TestWhenChargeProcessingSucceed:

    def setup_method(self):
        self.charge = Charge(
            order_id=1,
            amount_paid=150,
            payment_date=datetime.now(timezone.utc).date(),
            status=Charge.NOT_PROCESSED,
            funding_instrument=None,
            buyer=None,
        )
        order = Order(
            hash_id=uuid.uuid4(),
            talent_id=1,
            video_is_for='someone_else',
            is_from='Customer',
            is_to='Someone',
            instruction="Go Get 'em, Tiger",
            email='customer@viggio.com.br',
            is_public=True,
            charge=self.charge,
        )
        self.unit_of_work = PaymentProcessFakeUnitOfWork()
        data = dict(DATA)
        command = RequestShoutoutCommand(**data)
        process_payment(command, self.unit_of_work, FakeDBView(order))

    def test_it_should_set_processing_status(self):
        assert self.charge.status == Charge.PROCESSING


class TestWhenChargeProcessingFails:

    def setup_method(self):
        self.charge = Charge(
            order_id=1,
            amount_paid=150,
            payment_date=datetime.now(timezone.utc).date(),
            status=Charge.NOT_PROCESSED,
            funding_instrument=None,
            buyer=None,
        )
        order = Order(
            hash_id=uuid.uuid4(),
            talent_id=1,
            video_is_for='someone_else',
            is_from='Customer',
            is_to='Someone',
            instruction="Go Get 'em, Tiger",
            email='customer@viggio.com.br',
            is_public=True,
            charge=self.charge,
        )
        self.unit_of_work = PaymentProcessFakeUnitOfWork()
        data = dict(DATA)
        self.charge.amount_paid = 10001  # just for sake of testing
        command = RequestShoutoutCommand(**data)
        process_payment(command, self.unit_of_work, FakeDBView(order))

    def test_it_should_set_failed_status(self):
        assert self.charge.status == Charge.FAILED


class TestWhenAShoutoutIsSuccessfullyRequested:

    def setup_method(self):
        self.sent = []
        self.email_sender = EmailSender(fake_sender(self.sent))
        charge = Charge(
            order_id=1,
            amount_paid=150,
            payment_date=datetime.now(timezone.utc).date(),
            status=Charge.PAID,
            funding_instrument=None,
            buyer=None,
        )
        order = Order(
            hash_id=uuid.uuid4(),
            talent_id=1,
            video_is_for='someone_else',
            is_from='Customer',
            is_to='Someone',
            instruction="Go Get 'em, Tiger",
            email='customer@viggio.com.br',
            is_public=True,
            charge=charge,
        )
        order.created_at = datetime.now(timezone.utc)
        self.talent = mock.Mock()
        self.talent.user.email = 'talent@viggio.com.br'
        self.talent.user.get_full_name.return_value = 'Full Name'
        self.talent.profile_url = '/perfil/'
        self.event = ShoutoutSuccessfullyRequestedEvent(order)

    def test_it_should_send_order_info_to_customer(self):
        send_info_to_customer_about_his_shoutout_request(
            self.event,
            self.email_sender,
            FakeDBView(self.talent),
        )
        assert self.sent[0].to_email == 'Customer <customer@viggio.com.br>'

    def test_it_should_notify_talent(self):
        notify_talent_about_new_shoutout_request(
            self.event,
            self.email_sender,
            FakeDBView(self.talent),
        )
        assert self.sent[0].to_email == 'Full Name <talent@viggio.com.br>'
