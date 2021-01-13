import base64
import json
import os
import requests
from collections import namedtuple

from .models import WirecardTransactionData


WirecardOrder = namedtuple('WirecardOrder', 'id status')
WirecardPayment = namedtuple('WirecardPayment', 'id status')


def _get_headers():
    secret = f'{os.environ["WIRECARD_TOKEN"]}:{os.environ["WIRECARD_API_KEY"]}'
    digest = base64.b64encode(bytes(secret, 'utf-8'))
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {digest.decode()}',
    }
    return headers


class WirecardCreateOrderApiError(Exception):
    pass


class WirecardCreatePaymentApiError(Exception):
    pass


class WirecardCapturePaymentApiError(Exception):
    pass


class OrderApi:

    def __init__(self, http_handler=None):
        self.http_handler = http_handler or requests

    def create(self, order_data):
        payload = {
            'ownId': str(order_data.hash_id),
            'amount': {
                'currency': 'BRL',
            },
            'items': [
                {
                    'product': 'viggio',
                    'quantity': 1,
                    'category': 'ARTS_AND_ENTERTAINMENT',
                    'price': int(order_data.charge.amount_paid) * 100
                }
            ],
            'customer': {
                # ownId value is not supposed to be used, we are just sending in order to avoid
                # wirecard bitching about it
                'ownId': order_data.hash_id.node,
                'fullname': order_data.charge.buyer.fullname,
                'email': order_data.email,
                'birthDate': order_data.charge.buyer.birthdate.isoformat(),
                'taxDocument': {
                    'type': 'CPF',
                    'number': order_data.charge.buyer.tax_document,
                },
                'phone': {
                    'countryCode': '55',
                    'areaCode': order_data.charge.buyer.area_code,
                    'number': order_data.charge.buyer.phone_number,
                },
                # shippingAddress needs to be sent because it was the only way to make it work
                # during homologation, there must be some bug on the wirecard side
                'shippingAddress': {
                    'city': 'São Paulo',
                    'district': 'Centro Histórico de São Paulo',
                    'street': 'Praça da Sé',
                    'streetNumber': '68',
                    'zipCode': '01001001',
                    'state': 'SP',
                    'country': 'BRA'
                },
            },
        }
        response = self.http_handler.post(
            url=os.environ['WIRECARD_CREATE_ORDER_URL'],
            data=json.dumps(payload),
            headers=_get_headers(),
        )
        if not response.status_code == 201:
            raise WirecardCreateOrderApiError(
                f'{response.status_code} - {response.content.decode("utf-8")}'
            )
        data = response.json()
        if not data['status'] == 'CREATED':
            raise WirecardCreateOrderApiError(
                f'{response.status_code} - {response.content.decode("utf-8")}'
            )
        return WirecardOrder(id=data['id'], status=data['status'])


class PaymentApi:

    def __init__(self, http_handler=None):
        self.http_handler = http_handler or requests

    def create(self, order_data, wirecard_order_hash, delay_capture=False):
        payload = {
            'statementDescriptor': 'viggio.com.br',
            'installmentCount': 1,
            'delayCapture': delay_capture,
            'fundingInstrument': {
                'method': 'CREDIT_CARD',
                'creditCard': {
                    'hash': order_data.charge.funding_instrument.credit_card_hash,
                    'store': False,
                    'holder': {
                        'fullname': order_data.charge.funding_instrument.fullname,
                        'birthdate': order_data.charge.funding_instrument.birthdate.isoformat(),
                        'taxDocument': {
                            'type': 'CPF',
                            'number': order_data.charge.funding_instrument.tax_document,
                        },
                        'phone': {
                            'countryCode': '55',
                            'areaCode': order_data.charge.funding_instrument.area_code,
                            'number': order_data.charge.funding_instrument.phone_number,
                        }
                    }
                }
            }
        }
        response = self.http_handler.post(
            url=os.environ['WIRECARD_CREATE_PAYMENT_URL'].format(wirecard_order_hash),
            data=json.dumps(payload),
            headers=_get_headers(),
        )
        if not response.status_code == 201:
            raise WirecardCreatePaymentApiError(
                f'{response.status_code} - {response.content.decode("utf-8")}'
            )
        data = response.json()
        if data['status'] in ('CANCELLED', 'REFUNDED', 'REVERSED'):
            raise WirecardCreatePaymentApiError(
                f'{response.status_code} - {response.content.decode("utf-8")}'
            )
        return WirecardPayment(id=data['id'], status=data['status'])


class CapturePaymentApi:

    def __init__(self, http_handler=None):
        self.http_handler = http_handler or requests

    def capture(self, wirecard_payment_hash):
        response = self.http_handler.post(
            url=os.environ['WIRECARD_CAPTURE_PAYMENT_URL'].format(wirecard_payment_hash),
            headers=_get_headers(),
        )
        if not response.status_code == 200:
            raise WirecardCapturePaymentApiError(
                f'{response.status_code} - {response.content.decode("utf-8")}'
            )
        data = response.json()
        return WirecardPayment(id=data['id'], status=data['status'])


class WirecardOrderApi:

    def __init__(self, order_api, payment_api):
        self.order_api = order_api
        self.payment_api = payment_api

    def create_order(self, order_data):
        return self.order_api.create(order_data)

    def create_payment(self, order_data, wirecard_order_hash, delay_capture):
        return self.payment_api.create(order_data, wirecard_order_hash, delay_capture)

    def persist_transaction_data(self, order, wirecard_order_hash, wirecard_payment_hash):
        WirecardTransactionData.objects.create(
            order_id=order.id,
            wirecard_order_hash=wirecard_order_hash,
            wirecard_payment_hash=wirecard_payment_hash,
        )


class WirecardPaymentApi:

    def __init__(self, capture_payment_api):
        self.capture_payment_api = capture_payment_api

    def capture_payment(self, wirecard_payment_hash):
        return self.capture_payment_api.capture(wirecard_payment_hash)
