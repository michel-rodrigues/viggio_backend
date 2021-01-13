import pytest
import tempfile
import uuid
from collections import namedtuple
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from functools import partial
from unittest import mock

from request_shoutout.domain.emails.sender import EmailSender
from request_shoutout.domain.factories import AgencyProfitFactory, TalentProfitFactory
from request_shoutout.domain.messages import (
    FulfillShoutoutRequestCommand,
    ShoutoutSuccessfullyTranscodedEvent,
)
from request_shoutout.domain.models import (
    AgencyProfit,
    AgencyProfitPercentage,
    Charge,
    TalentProfit,
    Order,
    OrderExpiredError,
    OrderHasShoutoutError,
    Shoutout,
    TalentPermissionError,
    TalentProfitPercentage,
)
from request_shoutout.services.fulfill_shoutout_request import (
    fulfill_shoutout_request,
    notify_customer_about_shoutout_request_fulfilled,
    validate_order_can_be_fulfilled,
)
from request_shoutout.tests.fakes.adapters import (
    fake_sender,
    FulfillShoutoutRequestFakeUnitOfWork,
)
from request_shoutout.tests.fakes.db_views import FakeDBView
from request_shoutout.tests.fakes.factories import (
    fake_agency_profit_factory,
    fake_talent_profit_factory,
)


ORDER_HASH = uuid.uuid4()
SHOUTOUT_HASH = uuid.uuid4()

ORDER_DATA = {
    'id': 1,
    'hash_id': ORDER_HASH,
    'talent_id': 1,
    'video_is_for': 'someone_else',
    'is_from': 'Jailson',
    'is_to': 'Aquele cara do bar',
    'instruction': 'Aiiii que delícia cara!',
    'email': 'jailson@paidefamilia.io',
    'is_public': True,
    'charge': None,
}

COMMAND_DATA = {
    'order_hash': ORDER_HASH,
    'shoutout_hash': SHOUTOUT_HASH,
    'video_file': tempfile.NamedTemporaryFile(prefix='shoutout', suffix='.mp4'),
    'talent_id': 1,
}


class TestWhenOrderIsValidToBeFullfiled:

    def setup_method(self):
        self.order = Order(**ORDER_DATA)
        self.order.shoutout = None
        self.command = FulfillShoutoutRequestCommand(**COMMAND_DATA)

    def test_it_should_pass_without_raise_exception(self):
        validate_order_can_be_fulfilled(self.command, FakeDBView(self.order))


class TestWhenOrderIsInvalidToBeFullfiled:

    def setup_method(self):
        self.order = Order(**ORDER_DATA)
        self.order.shoutout = None
        self.command = FulfillShoutoutRequestCommand(**COMMAND_DATA)

    def test_it_should_raise_exception_when_order_has_a_shoutout_attached(self):
        self.order.shoutout = tempfile.NamedTemporaryFile(prefix='shoutout', suffix='.mp4')
        with pytest.raises(OrderHasShoutoutError):
            validate_order_can_be_fulfilled(self.command, FakeDBView(self.order))

    def test_it_should_raise_exception_when_order_has_expired(self):
        self.order.expiration_datetime = datetime.now(timezone.utc) - timedelta(hours=1)
        with pytest.raises(OrderExpiredError):
            validate_order_can_be_fulfilled(self.command, FakeDBView(self.order))

    def test_it_should_raise_exception_when_two_scenarios_happen_at_the_same_time(self):
        self.order.shoutout = tempfile.NamedTemporaryFile(prefix='shoutout', suffix='.mp4')
        self.order.expiration_datetime = datetime.now(timezone.utc) - timedelta(hours=1)
        with pytest.raises(OrderExpiredError):
            validate_order_can_be_fulfilled(self.command, FakeDBView(self.order))

    def test_it_should_raise_exception_when_order_is_to_another_talent(self):
        self.order.talent_id = self.order.talent_id + 100
        with pytest.raises(TalentPermissionError):
            validate_order_can_be_fulfilled(self.command, FakeDBView(self.order))


class TestWhenFulfillingAShoutoutRequest:

    def setup_method(self):
        self.amount_paid = Decimal('1000')
        charge = Charge(self.amount_paid, None, None, None, None)
        order_data = dict(ORDER_DATA)
        order_data['charge'] = charge
        self.order = Order(**order_data)
        talent_profit = TalentProfit(
            talent_id=order_data['talent_id'],
            order_id=order_data['id'],
            shoutout_price=self.amount_paid,
            profit_percentage=Decimal('0.75'),
            profit=Decimal('750.00'),
            paid=False,
        )
        Talent = namedtuple('fake_talent', 'agency_id')
        talent = Talent(None)
        self.unit_of_work = FulfillShoutoutRequestFakeUnitOfWork()
        command = FulfillShoutoutRequestCommand(**COMMAND_DATA)
        fulfill_shoutout_request(
            command,
            self.unit_of_work,
            FakeDBView(self.order),
            FakeDBView(talent),
            partial(fake_talent_profit_factory, talent_profit=talent_profit),
            None,
        )

    def test_it_should_create_a_new_shoutout(self):
        assert self.unit_of_work.shoutout is not None

    def test_shoutout_should_have_order_id_talent_id_and_file(self):
        assert self.unit_of_work.shoutout.order_id == 1
        assert self.unit_of_work.shoutout.talent_id == 1
        assert self.unit_of_work.shoutout.video_file == COMMAND_DATA['video_file']

    def test_it_should_attach_a_shoutout_to_order(self):
        assert self.order.shoutout == self.unit_of_work.shoutout

    def test_it_should_create_new_talent_profit(self):
        assert self.unit_of_work.talent_profit is not None

    def test_it_should_calculate_talent_profit(self):
        assert self.unit_of_work.talent_profit.shoutout_price == self.amount_paid
        assert self.unit_of_work.talent_profit.profit == Decimal('750.00')
        assert self.unit_of_work.talent_profit.profit_percentage == Decimal('0.75')

    def test_talent_profit_should_have_order_id_talent_id_and_not_paid_status(self):
        assert self.unit_of_work.talent_profit.order_id == 1
        assert self.unit_of_work.talent_profit.talent_id == 1
        assert self.unit_of_work.talent_profit.paid is False

    def test_it_should_committ_the_unit_of_work(self):
        assert self.unit_of_work.was_committed is True


class TestWhenAManagedTalentFulfillingAShoutoutRequest:

    def setup_method(self):
        self.amount_paid = Decimal('1000')
        charge = Charge(self.amount_paid, None, None, None, None)
        order_data = dict(ORDER_DATA)
        order_data['charge'] = charge
        self.order = Order(**order_data)
        talent_profit = TalentProfit(
            talent_id=order_data['talent_id'],
            order_id=order_data['id'],
            shoutout_price=self.amount_paid,
            profit_percentage=Decimal('0.75'),
            profit=Decimal('750.00'),
            paid=False,
        )
        agency_profit = AgencyProfit(
            agency_id=2,
            order_id=order_data['id'],
            shoutout_price=self.amount_paid,
            profit_percentage=Decimal('0.05'),
            profit=Decimal('50.00'),
            paid=False,
        )
        Talent = namedtuple('fake_talent', 'agency_id')
        talent = Talent(2)
        self.unit_of_work = FulfillShoutoutRequestFakeUnitOfWork()
        command = FulfillShoutoutRequestCommand(**COMMAND_DATA)
        fulfill_shoutout_request(
            command,
            self.unit_of_work,
            FakeDBView(self.order),
            FakeDBView(talent),
            partial(fake_talent_profit_factory, talent_profit=talent_profit),
            partial(fake_agency_profit_factory, agency_profit=agency_profit),
        )

    def test_it_should_create_new_talent_profit(self):
        assert self.unit_of_work.agency_profit is not None

    def test_it_should_calculate_agency_profit(self):
        assert self.unit_of_work.agency_profit.shoutout_price == self.amount_paid
        assert self.unit_of_work.agency_profit.profit == Decimal('50.00')
        assert self.unit_of_work.agency_profit.profit_percentage == Decimal('0.05')

    def test_agency_profit_should_have_order_id_talent_id_and_not_paid_status(self):
        assert self.unit_of_work.agency_profit.order_id == 1
        assert self.unit_of_work.agency_profit.agency_id == 2
        assert self.unit_of_work.agency_profit.paid is False


class TestWhenShoutoutVideoSuccessfullyTranscoded:

    def setup_method(self):
        self.sent = []
        self.email_sender = EmailSender(fake_sender(self.sent))
        charge = Charge(
            amount_paid=150,
            payment_date=datetime.now(timezone.utc).date(),
            status=Charge.PAID,
            funding_instrument=None,
            buyer=None,
        )
        order = Order(
            id=1,
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
        shoutout = Shoutout(
            hash_id=SHOUTOUT_HASH,
            order_id=order.id,
            video_file=COMMAND_DATA['video_file'],
            talent_id=COMMAND_DATA['talent_id'],
        )
        shoutout.order_hash = order.hash_id
        order.shoutout = shoutout
        user = mock.Mock()
        user.get_full_name.return_value = 'Full Name'
        Talent = namedtuple('fake_talent', 'user')
        talent = Talent(user)
        event = ShoutoutSuccessfullyTranscodedEvent(order.id)
        notify_customer_about_shoutout_request_fulfilled(
            event,
            self.email_sender,
            FakeDBView(order),
            FakeDBView(talent),
        )

    def test_it_should_send_one_email(self):
        assert len(self.sent) == 1

    def test_it_should_send_to_customer(self):
        assert self.sent[0].to_email == 'Customer <customer@viggio.com.br>'


class TestWhenBuildingTalentProfitObjectWithDefaultProfitPercentage:

    def setup_method(self):
        self.amount_paid = Decimal('1000')
        charge = Charge(self.amount_paid, None, None, None, None)
        order_data = dict(ORDER_DATA)
        order_data['charge'] = charge
        self.order = Order(**order_data)
        view_default_percentage = FakeDBView(
            TalentProfitPercentage(talent_id=None, value=Decimal('0.75'))
        )
        view_customized_percentage = FakeDBView(None)
        talent_profit_factory = TalentProfitFactory(
            view_customized_percentage,
            view_default_percentage,
        )
        self.talent_profit = talent_profit_factory(self.order)

    def test_it_should_calculate_talent_profit(self):
        assert self.talent_profit.shoutout_price == self.amount_paid
        assert self.talent_profit.profit == Decimal('750.00')
        assert self.talent_profit.profit_percentage == Decimal('0.75')

    def test_talent_profit_should_have_order_id_talent_id_and_not_paid_status(self):
        assert self.talent_profit.order_id == 1
        assert self.talent_profit.talent_id == 1
        assert self.talent_profit.paid is False


class TestWhenBuildingTalentProfitObjectWithCustomProfitPercentage:

    def setup_method(self):
        self.amount_paid = Decimal('1000')
        charge = Charge(self.amount_paid, None, None, None, None)
        order_data = dict(ORDER_DATA)
        order_data['charge'] = charge
        self.order = Order(**order_data)
        view_default_percentage = FakeDBView(
            obj=TalentProfitPercentage(talent_id=None, value=Decimal('0.75')),
        )
        view_customized_percentage = FakeDBView(
            obj=TalentProfitPercentage(talent_id=None, value=Decimal('0.80')),
        )
        talent_profit_factory = TalentProfitFactory(
            view_customized_percentage,
            view_default_percentage,
        )
        self.talent_profit = talent_profit_factory(self.order)

    def test_it_should_calculate_talent_profit(self):
        assert self.talent_profit.shoutout_price == self.amount_paid
        assert self.talent_profit.profit == Decimal('800.00')
        assert self.talent_profit.profit_percentage == Decimal('0.80')

    def test_talent_profit_should_have_order_id_talent_id_and_not_paid_status(self):
        assert self.talent_profit.order_id == 1
        assert self.talent_profit.talent_id == 1
        assert self.talent_profit.paid is False


class TestWhenBuildingAgencyProfit:

    def setup_method(self):
        self.amount_paid = Decimal('1000')
        charge = Charge(self.amount_paid, None, None, None, None)
        order_data = dict(ORDER_DATA)
        order_data['charge'] = charge
        self.order = Order(**order_data)
        view_agency_percentage = FakeDBView(
            AgencyProfitPercentage(agency_id=1, value=Decimal('0.05'))
        )
        agency_profit_factory = AgencyProfitFactory(view_agency_percentage)
        self.agency_profit = agency_profit_factory(order=self.order, agency_id=1)

    def test_it_should_calculate_agency_profit(self):
        assert self.agency_profit.shoutout_price == self.amount_paid
        assert self.agency_profit.profit == Decimal('50.00')
        assert self.agency_profit.profit_percentage == Decimal('0.05')

    def test_agency_profit_should_have_order_id_talent_id_and_not_paid_status(self):
        assert self.agency_profit.order_id == 1
        assert self.agency_profit.agency_id == 1
        assert self.agency_profit.paid is False
