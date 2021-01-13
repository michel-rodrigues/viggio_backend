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


class OrderListByTalentTest(APITestCase):

    def do_login(self, user, password):
        data = {
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'password': password,
        }
        response = self.client.post(reverse('accounts:signin'), data, format='json')
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def setUp(self):
        self.maxDiff = None
        password = 'senha123'
        user_1 = User(
            email='talent_1@viggio.com.br',
            first_name='Nome',
            last_name='Sobrenome',
        )
        user_1.set_password(password)
        user_1.save()
        self.do_login(user_1, password)
        self.talent_1 = Talent.objects.create(
            user=user_1,
            phone_number=1,
            area_code=1,
            main_social_media='',
            social_media_username='',
            number_of_followers=1,
        )
        self.one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        self.order_data_1 = {
            'hash_id': uuid.uuid4(),
            'talent_id': self.talent_1.id,
            'video_is_for': 'someone_else',
            'is_from': 'MJ',
            'is_to': 'Peter',
            'instruction': "Go Get 'em, Tiger",
            'email': 'customer@viggio.com.br',
            'is_public': True,
            'expiration_datetime': self.one_hour_ago,
        }
        self.order_1 = Order.objects.create(**self.order_data_1)  # expired order
        self.charge_data_1 = {
            'order': self.order_1,
            'amount_paid': 150,
            'payment_date': self.one_hour_ago,
            'payment_method': 'credit_card',
            'status': DomainCharge.CANCELLED,
        }
        self.charge_1 = Charge.objects.create(**self.charge_data_1)

        self.four_days_by_now = datetime.now(timezone.utc) + timedelta(days=4)
        self.order_data_4 = dict(self.order_data_1)
        self.order_data_4['expiration_datetime'] = self.four_days_by_now
        self.order_data_4['hash_id'] = uuid.uuid4()
        self.order_4 = Order.objects.create(**self.order_data_4)
        self.charge_data_4 = {
            'order': self.order_4,
            'amount_paid': 150,
            'payment_date': self.four_days_by_now,
            'payment_method': 'credit_card',
            'status': DomainCharge.PRE_AUTHORIZED,
        }

        self.charge_4 = Charge.objects.create(**self.charge_data_4)

        self.three_days_by_now = datetime.now(timezone.utc) + timedelta(days=3)
        self.order_data_3 = dict(self.order_data_4)
        self.order_data_3['expiration_datetime'] = self.three_days_by_now
        self.order_data_3['hash_id'] = uuid.uuid4()
        self.order_3 = Order.objects.create(**self.order_data_3)
        self.charge_data_3 = {
            'order': self.order_3,
            'amount_paid': 150,
            'payment_date': self.three_days_by_now,
            'payment_method': 'credit_card',
            'status': DomainCharge.PAID,
        }
        self.charge_3 = Charge.objects.create(**self.charge_data_3)

        self.two_days_by_now = datetime.now(timezone.utc) + timedelta(days=2)
        self.order_data_2 = dict(self.order_data_3)
        self.order_data_2['expiration_datetime'] = self.two_days_by_now
        self.order_data_2['hash_id'] = uuid.uuid4()
        self.order_2 = Order.objects.create(**self.order_data_2)
        self.charge_data_2 = {
            'order': self.order_2,
            'amount_paid': 150,
            'payment_date': self.two_days_by_now,
            'payment_method': 'credit_card',
            'status': DomainCharge.PRE_AUTHORIZED,
        }
        self.charge_2 = Charge.objects.create(**self.charge_data_2)

        # Some shit happened with webhook and the status were not updated
        self.order_data_5 = dict(self.order_data_2)
        self.order_data_5['expiration_datetime'] = self.one_hour_ago  # expired order
        self.order_data_5['hash_id'] = uuid.uuid4()
        self.order_5 = Order.objects.create(**self.order_data_5)
        self.charge_data_5 = {
            'order': self.order_5,
            'amount_paid': 150,
            'payment_date': self.two_days_by_now,
            'payment_method': 'credit_card',
            'status': DomainCharge.PRE_AUTHORIZED,
        }
        self.charge_5 = Charge.objects.create(**self.charge_data_5)

        user_2 = User.objects.create(
            email='talent_2@viggio.com.br',
            first_name='Nome',
            last_name='Sobrenome',
        )
        talent_2 = Talent.objects.create(
            user=user_2,
            phone_number=1,
            area_code=1,
            main_social_media='',
            social_media_username='',
            number_of_followers=1,
        )
        order_5 = Order.objects.create(
            hash_id=uuid.uuid4(),
            talent=talent_2,
            video_is_for='someone_else',
            is_from='MJ',
            is_to='Peter',
            instruction="Go Get 'em, Tiger",
            email='customer2@viggio.com.br',
            is_public=True,
            expiration_datetime=self.two_days_by_now,
        )
        charge_data_5 = {
            'order': order_5,
            'amount_paid': 150,
            'payment_date': self.two_days_by_now,
            'payment_method': 'credit_card',
            'status': DomainCharge.PRE_AUTHORIZED,
        }
        Charge.objects.create(**charge_data_5)

    def test_should_list_just_payment_pre_authorized_orders(self):
        self.order_data_2['expiration_datetime'] = (
            self.order_data_2['expiration_datetime'].isoformat().replace('+00:00', 'Z')
        )
        self.order_data_2['charge'] = {
            'amount_paid': '150.00',
            'payment_date': self.two_days_by_now.isoformat().replace('+00:00', 'Z'),
            'payment_method': 'credit_card',
            'status': DomainCharge.PRE_AUTHORIZED,
        }
        self.order_data_4['expiration_datetime'] = (
            self.order_data_4['expiration_datetime'].isoformat().replace('+00:00', 'Z')
        )
        self.order_data_4['charge'] = {
            'amount_paid': '150.00',
            'payment_date': self.four_days_by_now.isoformat().replace('+00:00', 'Z'),
            'payment_method': 'credit_card',
            'status': DomainCharge.PRE_AUTHORIZED,
        }
        self.order_data_2.pop('hash_id')
        self.order_data_2['order_hash'] = str(self.order_2.hash_id)
        self.order_data_4.pop('hash_id')
        self.order_data_4['order_hash'] = str(self.order_4.hash_id)

        expected_orders = [self.order_data_2, self.order_data_4]

        response = self.client.get(reverse('orders:talent_available_orders'), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected_orders)

    def test_should_list_just_not_fulfilled_orders(self):
        """Orders that already have a ShoutoutVideo attached, shouldn't be listed to Talent."""
        ShoutoutVideo.objects.create(
            hash_id=uuid.uuid4(),
            order=self.order_2,
            talent=self.talent_1,
            file=SimpleUploadedFile("file.mp4", b"filecontentstring"),
        )
        self.order_data_4['expiration_datetime'] = (
            self.order_data_4['expiration_datetime'].isoformat().replace('+00:00', 'Z')
        )
        self.order_data_4['charge'] = {
            'amount_paid': '150.00',
            'payment_date': self.four_days_by_now.isoformat().replace('+00:00', 'Z'),
            'payment_method': 'credit_card',
            'status': DomainCharge.PRE_AUTHORIZED,
        }
        self.order_data_4.pop('hash_id')
        self.order_data_4['order_hash'] = str(self.order_4.hash_id)

        expected_orders = [self.order_data_4]

        response = self.client.get(reverse('orders:talent_available_orders'), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected_orders)
