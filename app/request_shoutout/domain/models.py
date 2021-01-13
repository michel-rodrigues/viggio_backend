import os
from collections import namedtuple
from datetime import datetime, timedelta, timezone
from decimal import Decimal


EXPIRATION_DAYS = 5
SAFE_PERIOD = 1
SP_TZ = 3


class OrderExpiredError(Exception):
    pass


class TalentPermissionError(Exception):
    pass


class OrderHasShoutoutError(Exception):
    pass


class RequiredFieldError(Exception):
    pass


# TODO: criar um factory de Order
class Order:

    SOMEONE_ELSE = 'someone_else'
    MYSELF = 'myself'

    def __init__(
        self,
        hash_id,
        talent_id,
        video_is_for,
        is_from,
        is_to,
        instruction,
        email,
        is_public,
        charge,
        id=None,
    ):
        self.id = id
        self.hash_id = hash_id
        self.talent_id = talent_id
        self.video_is_for = video_is_for
        self._is_from = is_from
        self.is_to = is_to
        self.instruction = instruction
        self.email = email
        self.charge = charge
        self.is_public = is_public
        self.shoutout = None
        self._set_expiration_datetime()
        self._validate_video_is_for()

    def _validate_video_is_for(self):
        if self.video_is_for == Order.SOMEONE_ELSE and self._is_from is None:
            raise RequiredFieldError('is_from field is required when order is to someone else')

    def _set_expiration_datetime(self):
        expiration_datetime = (
            datetime.now(timezone.utc)
            + timedelta(days=EXPIRATION_DAYS)
        )
        self.expiration_datetime = expiration_datetime - timedelta(hours=SAFE_PERIOD)

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.email} - talent ID: {self.talent_id}>'

    @property
    def expired(self):
        return self.expiration_datetime < datetime.now(timezone.utc)

    @property
    def is_from(self):
        if not self._is_from and self.video_is_for == Order.MYSELF:
            return self.is_to
        return self._is_from

    @is_from.setter
    def is_from(self, value):
        self._is_from = value

    def validate_if_it_can_be_fulfilled(self, command):
        if self.expired:
            raise OrderExpiredError("Can't fulfill an expired order.")
        if not command.talent_id == self.talent_id:
            raise TalentPermissionError('Order belongs to another Talent.')
        if self.shoutout:
            raise OrderHasShoutoutError('Order already has a shoutout attached.')


class Buyer:
    def __init__(self, fullname, birthdate, tax_document, phone_number, area_code, charge_id=None):
        self.fullname = fullname
        self.birthdate = birthdate
        self.tax_document = tax_document
        self.area_code = area_code
        self.phone_number = phone_number
        self.charge_id = charge_id


class CreditCard:
    def __init__(
        self,
        fullname,
        birthdate,
        tax_document,
        phone_number,
        area_code,
        credit_card_hash,
        charge_id=None,
    ):
        self.fullname = fullname
        self.birthdate = birthdate
        self.tax_document = tax_document
        self.credit_card_hash = credit_card_hash
        self.area_code = area_code
        self.phone_number = phone_number
        self.charge_id = charge_id


class Charge:

    NOT_PROCESSED = 'not_processed'
    PROCESSING = 'processing'
    PRE_AUTHORIZED = 'pre_authorized'
    PAID = 'paid'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

    def __init__(
        self,
        amount_paid: Decimal,
        payment_date: datetime,
        status: bool,
        funding_instrument: CreditCard,
        buyer: Buyer,
        payment_method='credit_card',
        order_id=None,
    ):
        self.order_id = order_id
        self.amount_paid = Decimal(str(amount_paid)).quantize(Decimal('1.00'))
        self.payment_date = payment_date
        self.payment_method = payment_method
        self.status = status
        self.funding_instrument = funding_instrument
        self.buyer = buyer

    def set_failed_status(self):
        self.status = Charge.FAILED

    def set_processing_status(self):
        self.status = Charge.PROCESSING


class Shoutout:

    def __init__(self, hash_id, order_id, talent_id, video_file):
        self.hash_id = hash_id
        self.order_id = order_id
        self.talent_id = talent_id
        self.video_file = video_file

    def get_absolute_url(self):
        return f'{os.environ["SITE_URL"]}v/{self.hash_id}'


TalentProfitPercentage = namedtuple('TalentProfitPercentage', 'talent_id value')


class TalentProfit:

    def __init__(
        self,
        talent_id: int,
        order_id: int,
        shoutout_price: Decimal,
        profit_percentage: Decimal,
        profit: Decimal,
        paid: bool,
    ):
        self.talent_id = talent_id
        self.order_id = order_id
        self.shoutout_price = shoutout_price
        self.profit_percentage = profit_percentage
        self.profit = profit
        self.paid = paid
        self.payment_request_id = None


AgencyProfitPercentage = namedtuple('AgencyProfitPercentage', 'agency_id value')


class AgencyProfit:

    def __init__(
        self,
        agency_id: int,
        order_id: int,
        shoutout_price: Decimal,
        profit_percentage: Decimal,
        profit: Decimal,
        paid: bool,
    ):
        self.agency_id = agency_id
        self.order_id = order_id
        self.shoutout_price = shoutout_price
        self.profit_percentage = profit_percentage
        self.profit = profit
        self.paid = paid
        self.payment_request_id = None
