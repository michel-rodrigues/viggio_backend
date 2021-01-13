import uuid
from datetime import datetime, timedelta, timezone

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Charge, Order
from request_shoutout.domain.models import Charge as DomainCharge
from shoutouts.models import ShoutoutVideo
from talents.models import Talent


User = get_user_model()

ORDER_HASH = uuid.uuid4()
SHOUTOUT_HASH = uuid.uuid4()


class OrderDetailTest(APITestCase):

    def setUp(self):
        user = User.objects.create(
            email='talent@viggio.com.br',
            first_name='Nome',
            last_name='Sobrenome',
        )
        self.talent = Talent.objects.create(
            user=user,
            phone_number=1,
            area_code=1,
            main_social_media='',
            social_media_username='',
            number_of_followers=1,
        )
        self.tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        self.order = Order.objects.create(
            hash_id=ORDER_HASH,
            talent=self.talent,
            video_is_for='someone_else',
            is_from='MJ',
            is_to='Peter',
            instruction="Go Get 'em, Tiger",
            email='customer1@viggio.com.br',
            is_public=True,
            expiration_datetime=self.tomorrow,
        )
        self.charge_data = {
            'order': self.order,
            'amount_paid': 150,
            'payment_date': self.tomorrow,
            'payment_method': 'credit_card',
            'status': DomainCharge.PAID,
        }
        self.charge = Charge.objects.create(**self.charge_data)
        order_2 = Order.objects.create(
            hash_id=uuid.uuid4(),
            talent=self.talent,
            video_is_for='someone_else',
            is_from='MJ',
            is_to='Peter',
            instruction="Go Get 'em, Tiger",
            email='customer2@viggio.com.br',
            is_public=False,
            expiration_datetime=datetime.now(timezone.utc) + timedelta(days=2),
        )
        charge_data_2 = {
            'order': order_2,
            'amount_paid': 150,
            'payment_date': datetime.now(timezone.utc) - timedelta(days=2),
            'payment_method': 'credit_card',
            'status': DomainCharge.PAID,
        }
        self.charge = Charge.objects.create(**charge_data_2)

    def test_retrieving_order(self):
        response = self.client.get(
            reverse('orders:detail', kwargs={'order_hash': str(ORDER_HASH)}),
            format='json',
        )
        self.charge_data.pop('order')
        expected_order_data = {
            'order_hash': str(ORDER_HASH),
            'talent_id': self.talent.id,
            'video_is_for': 'someone_else',
            'is_from': 'MJ',
            'is_to': 'Peter',
            'instruction': "Go Get 'em, Tiger",
            'email': 'customer1@viggio.com.br',
            'is_public': True,
            'expiration_datetime': self.tomorrow.isoformat().replace('+00:00', 'Z'),
            'charge': {
                'amount_paid': '150.00',
                'payment_date': self.tomorrow.isoformat().replace('+00:00', 'Z'),
                'payment_method': 'credit_card',
                'status': DomainCharge.PAID,
            }
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected_order_data)

    def test_retrieving_order_with_shoutout_video(self):
        ShoutoutVideo.objects.create(
            hash_id=SHOUTOUT_HASH,
            order=self.order,
            talent=self.talent,
            file=SimpleUploadedFile("file.mp4", b"filecontentstring"),
        )
        response = self.client.get(
            reverse('orders:detail', kwargs={'order_hash': str(ORDER_HASH)}),
            format='json',
        )
        self.charge_data.pop('order')
        expected_order_data = {
            'order_hash': str(ORDER_HASH),
            'shoutout_hash': str(SHOUTOUT_HASH),
            'talent_id': self.talent.id,
            'video_is_for': 'someone_else',
            'is_from': 'MJ',
            'is_to': 'Peter',
            'instruction': "Go Get 'em, Tiger",
            'email': 'customer1@viggio.com.br',
            'is_public': True,
            'expiration_datetime': self.tomorrow.isoformat().replace('+00:00', 'Z'),
            'charge': {
                'amount_paid': '150.00',
                'payment_date': self.tomorrow.isoformat().replace('+00:00', 'Z'),
                'payment_method': 'credit_card',
                'status': DomainCharge.PAID,
            }
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected_order_data)
