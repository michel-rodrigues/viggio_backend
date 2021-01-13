import os
import json
import uuid
from collections import namedtuple
from datetime import date, datetime, timezone, timedelta
from dateutil.parser import parse
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import override_settings, TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Charge, Order
from request_shoutout.domain.models import (
    Buyer as DomainBuyer,
    Charge as DomainCharge,
    CreditCard as DomainCreditCard,
    Order as DomainOrder,
)
from talents.models import Talent
from .models import WirecardTransactionData
from .services import (
    _get_headers,
    CapturePaymentApi,
    OrderApi,
    PaymentApi,
    WirecardCapturePaymentApiError,
    WirecardCreateOrderApiError,
    WirecardCreatePaymentApiError,
)


User = get_user_model()
WirecardOrder = namedtuple('WirecardOrder', 'id status')
WirecardPayment = namedtuple('WirecardOrderecardPayment', 'id status')


FAKE_WIRECARD_ORDER_HASH = 'ORD-O5DLMAJZPTHV'
FAKE_WIRECARD_PAYMENT_HASH = 'PAY-HL7QRKFEQNHV'


class OrderTest(TestCase):

    def setUp(self):
        buyer = DomainBuyer(
            fullname='Mary Jane Watson',
            birthdate=date(2019, 12, 31),
            tax_document=12345678910,
            phone_number=987654321,
            area_code=11,
        )
        credit_card = DomainCreditCard(
            fullname='Mary Jane Watson',
            birthdate=date(2019, 12, 31),
            tax_document=12345678910,
            phone_number=654978321,
            area_code=12,
            credit_card_hash='<encrypted-credit-card-hash>',
        )
        charge = DomainCharge(
            amount_paid=150,
            status=DomainCharge.NOT_PROCESSED,
            payment_date=datetime.now(timezone.utc),
            funding_instrument=credit_card,
            buyer=buyer,
        )
        self.order = DomainOrder(
            hash_id=uuid.uuid4(),
            talent_id=-1,
            video_is_for='someone_else',
            is_from='MJ',
            is_to='Parker',
            instruction="Go Get 'em, Tiger",
            email='mary.jane.watson@spiderman.com',
            is_public=True,
            charge=charge,
        )

    def test_send_request_to_create_order_wirecard_api(self):
        wirecard_create_order_api_abriged_response = {
            'id': FAKE_WIRECARD_ORDER_HASH,
            'status': 'CREATED',
        }
        response = mock.Mock()
        response.status_code = 201
        response.json.return_value = wirecard_create_order_api_abriged_response
        mocked_http_handler = mock.Mock()
        mocked_http_handler.post.return_value = response
        order_api = OrderApi(mocked_http_handler)
        payload = {
            'ownId': str(self.order.hash_id),
            'amount': {
                'currency': 'BRL',
            },
            'items': [
                {
                    'product': 'viggio',
                    'quantity': 1,
                    'category': 'ARTS_AND_ENTERTAINMENT',
                    'price': 15000
                }
            ],
            'customer': {
                'ownId': self.order.hash_id.node,
                'fullname': self.order.charge.buyer.fullname,
                'email': self.order.email,
                'birthDate': self.order.charge.buyer.birthdate.isoformat(),
                'taxDocument': {
                    'type': 'CPF',
                    'number': self.order.charge.buyer.tax_document,
                },
                'phone': {
                    'countryCode': '55',
                    'areaCode': self.order.charge.buyer.area_code,
                    'number': self.order.charge.buyer.phone_number,
                },
                'shippingAddress': {
                    'city': 'São Paulo',
                    'district': 'Centro Histórico de São Paulo',
                    'street': 'Praça da Sé',
                    'streetNumber': '68',
                    'zipCode': '01001001',
                    'state': 'SP',
                    'country': 'BRA'
                },
            }
        }
        expected_call = mock.call(
            url='https://sandbox.moip.com.br/v2/orders',
            data=json.dumps(payload),
            headers=_get_headers(),
        )
        order_api.create(order_data=self.order)
        self.assertEqual(mocked_http_handler.post.mock_calls[0], expected_call)

    def test_wirecard_create_order_api_happy_path_response(self):
        wirecard_create_order_api_abriged_response = {
            'id': FAKE_WIRECARD_ORDER_HASH,
            'status': 'CREATED',
        }
        response = mock.Mock()
        response.status_code = 201
        response.json.return_value = wirecard_create_order_api_abriged_response
        mocked_http_handler = mock.Mock()
        mocked_http_handler.post.return_value = response
        order_api = OrderApi(mocked_http_handler)
        wirecard_order = order_api.create(order_data=self.order)
        self.assertEqual(wirecard_order, WirecardOrder(id=FAKE_WIRECARD_ORDER_HASH, status='CREATED'))

    def test_when_wirecard_create_order_api_response_status_code_is_not_201(self):
        response = mock.Mock()
        response.status_code = 500
        mocked_http_handler = mock.Mock()
        mocked_http_handler.post.return_value = response
        order_api = OrderApi(mocked_http_handler)
        with self.assertRaises(WirecardCreateOrderApiError):
            order_api.create(order_data=self.order)

    def test_when_order_status_is_not_created(self):
        wirecard_create_order_api_abriged_response = {
            'id': FAKE_WIRECARD_ORDER_HASH,
            'status': 'NOT_PAID',
        }
        response = mock.Mock()
        response.status_code = 201
        response.json.return_value = wirecard_create_order_api_abriged_response
        mocked_http_handler = mock.Mock()
        mocked_http_handler.post.return_value = response
        order_api = OrderApi(mocked_http_handler)
        with self.assertRaises(WirecardCreateOrderApiError):
            order_api.create(order_data=self.order)


class PaymentTest(TestCase):

    def setUp(self):
        buyer = DomainBuyer(
            fullname='Mary Jane Watson',
            birthdate=date(2019, 12, 31),
            tax_document=12345678910,
            phone_number=987654321,
            area_code=11,
        )
        credit_card = DomainCreditCard(
            fullname='Mary Jane Watson',
            birthdate=date(2019, 12, 31),
            tax_document=12345678910,
            phone_number=654978321,
            area_code=12,
            credit_card_hash='<encrypted-credit-card-hash>',
        )
        charge = DomainCharge(
            amount_paid=150,
            status=DomainCharge.NOT_PROCESSED,
            payment_date=datetime.now(timezone.utc),
            funding_instrument=credit_card,
            buyer=buyer,
        )
        self.order = DomainOrder(
            hash_id=uuid.uuid4(),
            talent_id=-1,
            video_is_for='someone_else',
            is_from='MJ',
            is_to='Parker',
            instruction="Go Get 'em, Tiger",
            email='mary.jane.watson@spiderman.com',
            is_public=True,
            charge=charge,
        )

    def test_send_request_to_create_payment_wirecard_api(self):
        wirecard_create_payment_api_abriged_response = {
            'id': FAKE_WIRECARD_PAYMENT_HASH,
            'status': 'IN_ANALYSIS',
        }
        response = mock.Mock()
        response.status_code = 201
        response.json.return_value = wirecard_create_payment_api_abriged_response
        mocked_http_handler = mock.Mock()
        mocked_http_handler.post.return_value = response
        payment_api = PaymentApi(mocked_http_handler)
        payload = {
            'statementDescriptor': 'viggio.com.br',
            'installmentCount': 1,
            'delayCapture': True,
            'fundingInstrument': {
                'method': 'CREDIT_CARD',
                'creditCard': {
                    'hash': self.order.charge.funding_instrument.credit_card_hash,
                    'store': False,
                    'holder': {
                        'fullname': self.order.charge.funding_instrument.fullname,
                        'birthdate': self.order.charge.funding_instrument.birthdate.isoformat(),
                        'taxDocument': {
                            'type': 'CPF',
                            'number': self.order.charge.funding_instrument.tax_document,
                        },
                        'phone': {
                            'countryCode': '55',
                            'areaCode': self.order.charge.funding_instrument.area_code,
                            'number': self.order.charge.funding_instrument.phone_number,
                        }
                    }
                }
            }
        }
        expected_call = mock.call(
            url=f'https://sandbox.moip.com.br/v2/orders/{FAKE_WIRECARD_ORDER_HASH}/payments',
            data=json.dumps(payload),
            headers=_get_headers(),
        )
        payment_api.create(
            order_data=self.order,
            wirecard_order_hash=FAKE_WIRECARD_ORDER_HASH,
            delay_capture=True,
        )
        self.assertEqual(mocked_http_handler.post.mock_calls[0], expected_call)

    def test_wirecard_create_payment_api_happy_path_response(self):
        wirecard_create_payment_api_abriged_response = {
            'id': FAKE_WIRECARD_PAYMENT_HASH,
            'status': 'IN_ANALYSIS',
        }
        response = mock.Mock()
        response.status_code = 201
        response.json.return_value = wirecard_create_payment_api_abriged_response
        mocked_http_handler = mock.Mock()
        mocked_http_handler.post.return_value = response
        payment_api = PaymentApi(mocked_http_handler)
        wirecard_payment = payment_api.create(
            order_data=self.order,
            wirecard_order_hash=FAKE_WIRECARD_ORDER_HASH,
            delay_capture=True,
        )
        self.assertEqual(
            wirecard_payment,
            WirecardPayment(id=FAKE_WIRECARD_PAYMENT_HASH, status='IN_ANALYSIS'),
        )

    def test_when_wirecard_create_payment_api_response_status_code_is_not_201(self):
        response = mock.Mock()
        response.status_code = 500
        mocked_http_handler = mock.Mock()
        mocked_http_handler.post.return_value = response
        payment_api = PaymentApi(mocked_http_handler)
        with self.assertRaises(WirecardCreatePaymentApiError):
            payment_api.create(
                order_data=self.order,
                wirecard_order_hash=FAKE_WIRECARD_ORDER_HASH,
                delay_capture=True,
            )

    def test_when_receive_an_unexpected_payment_status(self):
        wirecard_create_payment_api_abriged_response = {
            'id': FAKE_WIRECARD_PAYMENT_HASH,
            'status': 'CANCELLED',
        }
        response = mock.Mock()
        response.status_code = 201
        response.json.return_value = wirecard_create_payment_api_abriged_response
        mocked_http_handler = mock.Mock()
        mocked_http_handler.post.return_value = response
        payment_api = PaymentApi(mocked_http_handler)
        with self.assertRaises(WirecardCreatePaymentApiError):
            payment_api.create(
                order_data=self.order,
                wirecard_order_hash=FAKE_WIRECARD_ORDER_HASH,
                delay_capture=True,
            )


class CapturePaymentTest(TestCase):

    def setUp(self):
        buyer = DomainBuyer(
            fullname='Mary Jane Watson',
            birthdate=date(2019, 12, 31),
            tax_document=12345678910,
            phone_number=987654321,
            area_code=11,
        )
        credit_card = DomainCreditCard(
            fullname='Mary Jane Watson',
            birthdate=date(2019, 12, 31),
            tax_document=12345678910,
            phone_number=654978321,
            area_code=12,
            credit_card_hash='<encrypted-credit-card-hash>',
        )
        charge = DomainCharge(
            amount_paid=150,
            status=DomainCharge.NOT_PROCESSED,
            payment_date=datetime.now(timezone.utc),
            funding_instrument=credit_card,
            buyer=buyer,
        )
        self.order = DomainOrder(
            hash_id=uuid.uuid4(),
            talent_id=-1,
            video_is_for='someone_else',
            is_from='MJ',
            is_to='Parker',
            instruction="Go Get 'em, Tiger",
            email='mary.jane.watson@spiderman.com',
            is_public=True,
            charge=charge,
        )

    def test_send_request_to_capture_payment_wirecard_api(self):
        wirecard_capture_payment_api_abriged_response = {
            'id': FAKE_WIRECARD_PAYMENT_HASH,
            'status': 'AUTHORIZED',
        }
        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = wirecard_capture_payment_api_abriged_response
        mocked_http_handler = mock.Mock()
        mocked_http_handler.post.return_value = response
        capture_payment_api = CapturePaymentApi(mocked_http_handler)
        expected_call = mock.call(
            url=f'https://sandbox.moip.com.br/v2/payments/{FAKE_WIRECARD_PAYMENT_HASH}/capture',
            headers=_get_headers(),
        )
        capture_payment_api.capture(wirecard_payment_hash=FAKE_WIRECARD_PAYMENT_HASH)
        self.assertEqual(mocked_http_handler.post.mock_calls[0], expected_call)

    def test_wirecard_capture_payemnt_api_happy_path_response(self):
        wirecard_capture_payment_api_abriged_response = {
            'id': FAKE_WIRECARD_PAYMENT_HASH,
            'status': 'AUTHORIZED',
        }
        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = wirecard_capture_payment_api_abriged_response
        mocked_http_handler = mock.Mock()
        mocked_http_handler.post.return_value = response
        capture_payment_api = CapturePaymentApi(mocked_http_handler)
        wirecard_payment = capture_payment_api.capture(wirecard_payment_hash=FAKE_WIRECARD_PAYMENT_HASH)
        self.assertEqual(
            wirecard_payment,
            WirecardPayment(id=FAKE_WIRECARD_PAYMENT_HASH, status='AUTHORIZED'),
        )

    def test_when_wirecard_capture_payment_api_response_status_code_is_not_200(self):
        response = mock.Mock()
        response.status_code = 500
        mocked_http_handler = mock.Mock()
        mocked_http_handler.post.return_value = response
        capture_payment_api = CapturePaymentApi(mocked_http_handler)
        with self.assertRaises(WirecardCapturePaymentApiError):
            capture_payment_api.capture(wirecard_payment_hash=FAKE_WIRECARD_PAYMENT_HASH)


class WebhookPaymentTest(APITestCase):

    def setUp(self):
        user = User.objects.create(email='talent@youtuber.com')
        self.talent = Talent.objects.create(
            user=user,
            phone_number=1,
            area_code=1,
            main_social_media='',
            social_media_username='',
            number_of_followers=1,
        )
        self.order = Order.objects.create(
            hash_id=uuid.uuid4(),
            talent=self.talent,
            video_is_for='someone_else',
            is_from='MJ',
            is_to='Parker',
            instruction="Go Get 'em, Tiger",
            email='mary.jane.watson@spiderman.com',
            is_public=True,
            expiration_datetime=datetime.now(timezone.utc) + timedelta(days=5)
        )
        self.charge = Charge.objects.create(
            order=self.order,
            status=DomainCharge.PROCESSING,
            amount_paid='150',
            payment_method='credit_card',
            payment_date=datetime.now(timezone.utc) + timedelta(days=5),
        )
        self.wirecard_transaction_data = WirecardTransactionData.objects.create(
            order=self.order,
            wirecard_order_hash=FAKE_WIRECARD_ORDER_HASH,
            wirecard_payment_hash=FAKE_WIRECARD_PAYMENT_HASH,
        )

    @override_settings(
        task_eager_propagates=True,
        task_always_eager=True,
        broker_url='memory://',
        backend='memory',
    )
    def test_response_status_code_should_be_200_ok(self):
        webhook_payment_dummy_data = {
            "event": "PAYMENT.AUTHORIZED",
            "resource": {
                "payment": {
                    "events": [
                        {
                           "createdAt": "2017-10-23T15:08:39.718-02",
                           "type": "PAYMENT.AUTHORIZED"
                        },
                        {
                           "createdAt": "2017-10-23T15:08:39.000-02",
                           "type": "PAYMENT.IN_ANALYSIS"
                        },
                        {
                           "createdAt": "2017-10-23T15:08:09.000-02",
                           "type": "PAYMENT.CREATED"
                        }
                    ],
                    "id": FAKE_WIRECARD_PAYMENT_HASH,
                    "status": "AUTHORIZED",
                    "updatedAt": "2017-10-23T15:08:39.718-02"
                }
            }
        }
        self.client.credentials(HTTP_AUTHORIZATION=os.environ['WIRECARD_PAYMENT_WEBHOOK_TOKEN'])
        response = self.client.post(
            reverse('wirecard:webhook_payment'),
            webhook_payment_dummy_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_settings(
        task_eager_propagates=True,
        task_always_eager=True,
        broker_url='memory://',
        backend='memory',
    )
    def test_should_change_charge_status_to_pre_authorized(self):
        webhook_payment_dummy_data = {
            "event": "PAYMENT.PRE_AUTHORIZED",
            "resource": {
                "payment": {
                    "events": [
                        {
                           "createdAt": "2017-10-23T15:08:39.718-02",
                           "type": "PAYMENT.PRE_AUTHORIZED"
                        },
                        {
                           "createdAt": "2017-10-23T15:08:39.717-02",
                           "type": "PAYMENT.IN_ANALYSIS"
                        },
                        {
                           "createdAt": "2017-10-23T15:08:09.716-02",
                           "type": "PAYMENT.CREATED"
                        }
                    ],
                    "id": FAKE_WIRECARD_PAYMENT_HASH,
                    "status": "PRE_AUTHORIZED",
                    "updatedAt": "2017-10-23T15:08:39.718-02"
                }
            }
        }
        self.client.credentials(HTTP_AUTHORIZATION=os.environ['WIRECARD_PAYMENT_WEBHOOK_TOKEN'])
        self.client.post(
            reverse('wirecard:webhook_payment'),
            webhook_payment_dummy_data,
            format='json',
        )
        self.charge.refresh_from_db()
        self.assertEqual(self.charge.status, DomainCharge.PRE_AUTHORIZED)

    @override_settings(
        task_eager_propagates=True,
        task_always_eager=True,
        broker_url='memory://',
        backend='memory',
    )
    def test_should_save_last_event_timestamp(self):
        last_event_timestamp = "2017-10-23T15:08:39.717-02"
        webhook_payment_dummy_data = {
            "event": "PAYMENT.IN_ANALYSIS",
            "resource": {
                "payment": {
                    "events": [
                        {
                           "createdAt": last_event_timestamp,
                           "type": "PAYMENT.IN_ANALYSIS"
                        },
                        {
                           "createdAt": "2017-10-23T15:08:09.716-02",
                           "type": "PAYMENT.CREATED"
                        }
                    ],
                    "id": FAKE_WIRECARD_PAYMENT_HASH,
                    "status": "IN_ANALYSIS",
                    "updatedAt": last_event_timestamp
                }
            }
        }
        self.client.credentials(HTTP_AUTHORIZATION=os.environ['WIRECARD_PAYMENT_WEBHOOK_TOKEN'])
        self.client.post(
            reverse('wirecard:webhook_payment'),
            webhook_payment_dummy_data,
            format='json',
        )
        self.wirecard_transaction_data.refresh_from_db()
        self.assertEqual(
            self.wirecard_transaction_data.payment_event_last_timestamp,
            parse(last_event_timestamp)
        )

    @override_settings(
        task_eager_propagates=True,
        task_always_eager=True,
        broker_url='memory://',
        backend='memory',
    )
    def test_should_just_change_charge_status_when_is_the_last_payment_event(self):
        self.wirecard_transaction_data.payment_event_last_timestamp = (
            parse('2017-10-23T15:08:39.718-02')
        )
        self.wirecard_transaction_data.save()
        self.charge.status = DomainCharge.PRE_AUTHORIZED
        self.charge.save()
        # simulating a delayied notification request
        webhook_payment_dummy_data = {
            "event": "PAYMENT.IN_ANALYSIS",
            "resource": {
                "payment": {
                    "events": [
                        {
                           "createdAt": "2017-10-23T15:08:39.717-02",
                           "type": "PAYMENT.IN_ANALYSIS"
                        },
                        {
                           "createdAt": "2017-10-23T15:08:09.716-02",
                           "type": "PAYMENT.CREATED"
                        }
                    ],
                    "id": FAKE_WIRECARD_PAYMENT_HASH,
                    "status": "IN_ANALYSIS",
                    "updatedAt": "2017-10-23T15:08:39.717-02"
                }
            }
        }
        self.client.credentials(HTTP_AUTHORIZATION=os.environ['WIRECARD_PAYMENT_WEBHOOK_TOKEN'])
        self.client.post(
            reverse('wirecard:webhook_payment'),
            webhook_payment_dummy_data,
            format='json',
        )
        self.charge.refresh_from_db()
        self.assertEqual(self.charge.status, DomainCharge.PRE_AUTHORIZED)
