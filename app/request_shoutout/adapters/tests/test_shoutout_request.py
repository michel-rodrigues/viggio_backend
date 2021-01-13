import json
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from talents.models import Talent
from request_shoutout.domain.models import (
    Charge as DomainCharge,
    EXPIRATION_DAYS,
    SAFE_PERIOD,
    SP_TZ,
)
from orders.models import Buyer, Charge, CreditCard, Order
from wirecard.models import WirecardTransactionData
from wirecard.services import _get_headers

User = get_user_model()

FAKE_WIRECARD_ORDER_HASH = 'ORD-O5DLMAJZPTHV'
WIRECARD_PAYMENT_HASH = 'PAY-HL7QRKFEQNHV'


def get_wirecard_mocked_abriged_responses():
    wirecard_create_order_api_abriged_response = {
        'id': FAKE_WIRECARD_ORDER_HASH,
        'status': 'CREATED',
    }
    create_order_response = mock.Mock()
    create_order_response.status_code = 201
    create_order_response.json.return_value = wirecard_create_order_api_abriged_response

    wirecard_create_payment_api_abriged_response = {
        'id': WIRECARD_PAYMENT_HASH,
        'status': 'PRE_AUTHORIZED',
    }
    create_payment_response = mock.Mock()
    create_payment_response.status_code = 201
    create_payment_response.json.return_value = wirecard_create_payment_api_abriged_response
    return create_order_response, create_payment_response


@override_settings(
    task_eager_propagates=True,
    task_always_eager=True,
    broker_url='memory://',
    backend='memory'
)
@mock.patch('post_office.mailgun.requests')
@mock.patch('wirecard.services.requests.post', side_effect=get_wirecard_mocked_abriged_responses())
class ChargeShoutoutRequestTest(APITestCase):

    def setUp(self):
        self.talent_user = User.objects.create(
            email='talento@youtube.com',
            first_name='Nome',
            last_name='Sobrenome',
        )
        self.talent = Talent.objects.create(
            user=self.talent_user,
            price=150,
            phone_number=1,
            area_code=1,
            main_social_media='',
            social_media_username='',
            number_of_followers=1,
        )
        self.request_data = {
            'order_video_is_for': 'someone_else',
            'order_is_from': 'MJ',
            'order_is_to': 'Peter',
            'order_instruction': "Go Get 'em, Tiger",
            'order_email': 'mary.jane.watson@spiderman.com',
            'order_talent_id': self.talent.id,
            'order_amount_paid': 150,
            'order_is_not_public': False,
            'customer_fullname': 'Mary Jane Watson',
            'customer_birthdate': '31/12/2019',
            'customer_phone_number': '987654321',
            'customer_area_code': '11',
            'customer_tax_document': '01234567890',
            'credit_card_owner_fullname': 'Pater Parker',
            'credit_card_owner_birthdate': '31/12/2019',
            'credit_card_owner_phone_number': '123465798',
            'credit_card_owner_area_code': '11',
            'credit_card_owner_tax_document': '12345678910',
            'credit_card_hash': '<encrypted-credit-card-hash>',
            'not_my_cc': 'true',
        }

    def test_processing_a_shoutout_request_should_create_an_order(self, mock1, mock2):
        response = self.client.post(
            reverse('request_shoutout:charge'),
            self.request_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.hash_id, response.data['order_hash'])
        self.assertEqual(order.talent_id, self.request_data['order_talent_id'])
        self.assertEqual(order.video_is_for, self.request_data['order_video_is_for'])
        self.assertEqual(order.is_from, self.request_data['order_is_from'])
        self.assertEqual(order.is_to, self.request_data['order_is_to'])
        self.assertEqual(order.instruction, self.request_data['order_instruction'])
        self.assertEqual(order.email, self.request_data['order_email'])

    def test_processing_a_shoutout_request_should_create_a_charge(self, mock1, mock2):
        response = self.client.post(
            reverse('request_shoutout:charge'),
            self.request_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Charge.objects.count(), 1)
        charge = Charge.objects.first()
        self.assertEqual(charge.order, Order.objects.first())
        self.assertEqual(charge.amount_paid, Decimal('150.00'))
        self.assertEqual(charge.payment_date.date(), datetime.now(timezone.utc).date())
        self.assertEqual(charge.payment_method, 'credit_card')
        self.assertEqual(charge.status, DomainCharge.PROCESSING)

    def test_processing_a_shoutout_request_should_send_request_to_wirecard(self, wirecard_mocked_http_handler_post, mock2):  # noqa: E501
        """Payment process should send a request to Wirecard Order API and Wirecard Payment API"""
        response = self.client.post(
            reverse('request_shoutout:charge'),
            self.request_data,
            format='json',
        )

        wirecard_order_payload = {
            'ownId': str(response.data['order_hash']),
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
                'ownId': response.data['order_hash'].node,
                'fullname': self.request_data['customer_fullname'],
                'email': self.request_data['order_email'],
                'birthDate': '2019-12-31',
                'taxDocument': {
                    'type': 'CPF',
                    'number': self.request_data['customer_tax_document'],
                },
                'phone': {
                    'countryCode': '55',
                    'areaCode': self.request_data['customer_area_code'],
                    'number': self.request_data['customer_phone_number'],
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
        create_wirecard_order_expected_call = mock.call(
            url='https://sandbox.moip.com.br/v2/orders',
            data=json.dumps(wirecard_order_payload),
            headers=_get_headers(),
        )

        wirecard_payment_payload = {
            'statementDescriptor': 'viggio.com.br',
            'installmentCount': 1,
            'delayCapture': True,
            'fundingInstrument': {
                'method': 'CREDIT_CARD',
                'creditCard': {
                    'hash': self.request_data['credit_card_hash'],
                    'store': False,
                    'holder': {
                        'fullname': self.request_data['credit_card_owner_fullname'],
                        'birthdate': '2019-12-31',
                        'taxDocument': {
                            'type': 'CPF',
                            'number': self.request_data['credit_card_owner_tax_document'],
                        },
                        'phone': {
                            'countryCode': '55',
                            'areaCode': self.request_data['credit_card_owner_area_code'],
                            'number': self.request_data['credit_card_owner_phone_number'],
                        }
                    }
                }
            }
        }
        wirecard_order_id = FAKE_WIRECARD_ORDER_HASH
        create_wirecard_payment_expected_call = mock.call(
            url=f'https://sandbox.moip.com.br/v2/orders/{wirecard_order_id}/payments',
            data=json.dumps(wirecard_payment_payload),
            headers=_get_headers(),
        )

        wirecard_expected_calls = [
            create_wirecard_order_expected_call,
            create_wirecard_payment_expected_call,
        ]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(wirecard_mocked_http_handler_post.mock_calls, wirecard_expected_calls)

    def test_when_buyer_is_credit_card_owner_should_replicate_his_info(self, wirecard_mocked_http_handler_post, mock2):  # noqa: E501
        self.request_data['not_my_cc'] = 'false'
        self.request_data['credit_card_owner_fullname'] = 'Mary Jane Watson'
        self.request_data['credit_card_owner_birthdate'] = ''
        self.request_data['credit_card_owner_phone_number'] = ''
        self.request_data['credit_card_owner_area_code'] = ''
        self.request_data['credit_card_owner_tax_document'] = ''

        response = self.client.post(
            reverse('request_shoutout:charge'),
            self.request_data,
            format='json',
        )

        wirecard_order_payload = {
            'ownId': str(response.data['order_hash']),
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
                'ownId': response.data['order_hash'].node,
                'fullname': self.request_data['customer_fullname'],
                'email': self.request_data['order_email'],
                'birthDate': '2019-12-31',
                'taxDocument': {
                    'type': 'CPF',
                    'number': self.request_data['customer_tax_document'],
                },
                'phone': {
                    'countryCode': '55',
                    'areaCode': self.request_data['customer_area_code'],
                    'number': self.request_data['customer_phone_number'],
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
        create_wirecard_order_expected_call = mock.call(
            url='https://sandbox.moip.com.br/v2/orders',
            data=json.dumps(wirecard_order_payload),
            headers=_get_headers(),
        )

        wirecard_payment_payload = {
            'statementDescriptor': 'viggio.com.br',
            'installmentCount': 1,
            'delayCapture': True,
            'fundingInstrument': {
                'method': 'CREDIT_CARD',
                'creditCard': {
                    'hash': self.request_data['credit_card_hash'],
                    'store': False,
                    'holder': {
                        'fullname': self.request_data['customer_fullname'],
                        'birthdate': '2019-12-31',
                        'taxDocument': {
                            'type': 'CPF',
                            'number': self.request_data['customer_tax_document'],
                        },
                        'phone': {
                            'countryCode': '55',
                            'areaCode': self.request_data['customer_area_code'],
                            'number': self.request_data['customer_phone_number'],
                        }
                    }
                }
            }
        }
        wirecard_order_id = FAKE_WIRECARD_ORDER_HASH
        create_wirecard_payment_expected_call = mock.call(
            url=f'https://sandbox.moip.com.br/v2/orders/{wirecard_order_id}/payments',
            data=json.dumps(wirecard_payment_payload),
            headers=_get_headers(),
        )

        wirecard_expected_calls = [
            create_wirecard_order_expected_call,
            create_wirecard_payment_expected_call,
        ]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(wirecard_mocked_http_handler_post.mock_calls, wirecard_expected_calls)

    def test_processing_a_shoutout_request_should_create_a_wirecard_payment_data(self, mock1, mock2):  # noqa: E501
        response = self.client.post(
            reverse('request_shoutout:charge'),
            self.request_data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(WirecardTransactionData.objects.count(), 1)

        wirecard_card_data = WirecardTransactionData.objects.first()
        wirecard_card_data.order, Order.objects.first()

        self.assertEqual(wirecard_card_data.wirecard_order_hash, FAKE_WIRECARD_ORDER_HASH)
        self.assertEqual(wirecard_card_data.wirecard_payment_hash, WIRECARD_PAYMENT_HASH)

    def test_charging_a_shoutout_request_to_myself(self, mock1, mailgun_mocked_requests):
        """order_is_from field is not required when requesting shoutout to myself"""
        self.request_data['order_video_is_for'] = 'myself'
        self.request_data.pop('order_is_from')
        datetime_now = datetime.now(timezone.utc)
        order_utc_expiration_datetime = (
            (datetime_now + timedelta(days=EXPIRATION_DAYS))
            - timedelta(hours=SAFE_PERIOD)
        )
        order_expiration_datetime = order_utc_expiration_datetime - timedelta(hours=SP_TZ)
        expected_calls = [
            mock.call(
                auth=('api', os.environ['MAILGUN_API_KEY']),
                url=os.environ['MAILGUN_API_URL'],
                data={
                    'from': os.environ['CONTACT_EMAIL'],
                    'to': 'Peter <mary.jane.watson@spiderman.com>',
                    'subject': 'Seu pedido foi enviado para Nome Sobrenome',
                    'template': 'order-detail',
                    'v:customer_name': 'Peter',
                    'v:order_created_at': datetime_now.date().strftime('%d/%m/%Y'),
                    'v:talent_url': self.talent.profile_url,
                    'v:talent_name': 'Nome Sobrenome',
                    'v:order_instruction': "Go Get 'em, Tiger",
                    'v:charge_amout_paid': 150.0,
                    'v:order_expiration_datetime': (
                        order_expiration_datetime.strftime('%d/%m/%Y - %Hh')
                    ),
                },
            ),
            mock.call(
                auth=('api', os.environ['MAILGUN_API_KEY']),
                url=os.environ['MAILGUN_API_URL'],
                data={
                    'from': os.environ['CONTACT_EMAIL'],
                    'to': 'Nome Sobrenome <talento@youtube.com>',
                    'subject': 'Você tem um novo pedido',
                    'template': 'notify-talent-about-new-order',
                    'v:talent_name': 'Nome Sobrenome',
                    'v:order_created_at': datetime_now.strftime('%d/%m/%Y'),
                    'v:customer_name': 'Peter',
                    'v:order_instruction': "Go Get 'em, Tiger",
                    'v:charge_amout_paid': 150.0,
                    'v:order_expiration_datetime': (
                        order_expiration_datetime.strftime('%d/%m/%Y - %Hh')
                    ),
                    'v:order_is_to': 'Peter',
                    'v:dashboard_url': os.environ['SITE_URL'] + 'dashboard/',
                },
            ),
        ]
        response = self.client.post(
            reverse('request_shoutout:charge'),
            self.request_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.video_is_for, self.request_data['order_video_is_for'])
        self.assertEqual(order.is_from, 'Peter')
        self.assertEqual(mailgun_mocked_requests.post.mock_calls, expected_calls)

    def test_requesting_a_shoutout_with_field_is_not_public_checked(self, mock1, mailgun_mocked_requests):  # noqa: E501
        """When user check is_not_public field."""
        self.request_data['order_is_not_public'] = True
        response = self.client.post(
            reverse('request_shoutout:charge'),
            self.request_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.is_public, False)

    def test_requesting_a_shoutout_with_field_is_not_public_unchecked(self, mock1, mailgun_mocked_requests):  # noqa: E501
        self.request_data['order_is_not_public'] = False
        response = self.client.post(
            reverse('request_shoutout:charge'),
            self.request_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.is_public, True)

    def test_rollback_when_persisting_order_fails(self, mock1, mock2):
        method_path = 'request_shoutout.adapters.db.orm.DjangoBuyer.persist'
        with mock.patch(method_path, side_effect=Exception):
            response = self.client.post(
                reverse('request_shoutout:charge'),
                self.request_data,
                format='json',
            )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['error'], 'An issue happened while persisting data.')
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Charge.objects.count(), 0)
        self.assertEqual(CreditCard.objects.count(), 0)
        self.assertEqual(Buyer.objects.count(), 0)

    def test_when_charge_process_fails_charge_status_is_set_up_as_failed(self, mock1, mock2):
        method_path = 'request_shoutout.adapters.db.orm.WirecardOrderApi.persist_transaction_data'
        with mock.patch(method_path, side_effect=Exception):
            response = self.client.post(
                reverse('request_shoutout:charge'),
                self.request_data,
                format='json',
            )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['error'], 'An issue happened while processing payment.')
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Charge.objects.count(), 1)
        charge = Charge.objects.first()
        self.assertEqual(charge.status, DomainCharge.FAILED)
