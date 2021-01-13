import os
import tempfile
import uuid
from datetime import datetime, timezone, timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase


from categories.models import Category
from customers.models import Customer
from orders.models import Charge, Order
from request_shoutout.domain.models import Charge as DomainCharge
from shoutouts.models import ShoutoutVideo
from talents.models import Talent, PresentationVideo


User = get_user_model()


ORDER_1_HASH = uuid.uuid4()
ORDER_2_HASH = uuid.uuid4()

SHOUTOUT_1_HASH = uuid.uuid4()
SHOUTOUT_2_HASH = uuid.uuid4()


class UpdateTalentTest(APITestCase):

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

    def refresh_models_from_db(self):
        self.user.refresh_from_db()
        self.talent.refresh_from_db()
        self.customer.refresh_from_db()

    def setUp(self):
        password = 'senha123'
        self.user = User.objects.create(
            email='talent1@viggio.com.br',
            first_name='Nome',
            last_name='Sobrenome',
        )
        self.user.set_password(password)
        self.user.save()
        self.do_login(self.user, password)
        self.customer = Customer.objects.create(user=self.user)
        self.talent = Talent.objects.create(
            user=self.user,
            phone_number=1,
            area_code=1,
            main_social_media='',
            social_media_username='',
            number_of_followers=1,
        )
        self.category_1 = Category.objects.create(name='Youtubers', slug='youtubers')
        self.category_2 = Category.objects.create(name='Influencers', slug='influencers')
        self.category_3 = Category.objects.create(name='Charity', slug='charity')

    def test_retrieving_talent_info(self):
        self.customer.avatar = SimpleUploadedFile('avatar.jpg', b'filecontentstring')
        self.customer.save()
        self.talent.price = 150
        self.talent.description = 'Uma descrição boladona.'
        self.talent.available = True
        self.talent.area_code = 12
        self.talent.phone_number = 987654321
        self.talent.main_social_media = 'Instagram'
        self.talent.social_media_username = 'talent1'
        self.talent.number_of_followers = 1000
        self.talent.save()
        presentation_video = PresentationVideo.objects.create(
            talent=self.talent,
            file=SimpleUploadedFile('file.mp4', b'filecontentstring'),
        )
        self.talent.categories.add(self.category_1, self.category_2)
        expected_response_data = {
            'user_id': self.user.id,
            'email': 'talent1@viggio.com.br',
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'phone_number': '987654321',
            'area_code': '12',
            'main_social_media': 'Instagram',
            'social_media_username': 'talent1',
            'number_of_followers': 1000,
            'price': '150.00',
            'description': 'Uma descrição boladona.',
            'presentation_video': presentation_video.file.url,
            'available': True,
            'avatar': self.customer.avatar.url,
            'categories': [
                {
                    'name': self.category_1.name,
                    'slug': self.category_1.slug,
                },
                {
                    'name': self.category_2.name,
                    'slug': self.category_2.slug,
                },
            ]
        }
        response = self.client.get(reverse('talents:update'), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected_response_data)

    def test_updating_talent_data(self):
        data = {
            'email': 'talent1@viggio.com.br',
            'first_name': 'Novo Nome',
            'last_name': '',
            'avatar': '',
            'price': 150,
            'description': 'Uma descrição boladona.',
            'available': True,
            'area_code': '12',
            'phone_number': '987654321',
            'main_social_media': 'Instagram',
            'social_media_username': 'talent1',
            'number_of_followers': 1000,
            'presentation_video': SimpleUploadedFile('Comunicação.mp4', b'filecontentstring'),
            'categories': [],
        }
        image_tmp_file = tempfile.NamedTemporaryFile(prefix='Comunicação', suffix='.jpg')
        image = Image.new('RGB', (100, 100))
        image.save(image_tmp_file)
        with open(image_tmp_file.name, 'rb') as avatar:
            data['avatar'] = avatar
            response = self.client.put(reverse('talents:update'), data=data, format='multipart')
            avatar.seek(0)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('presentation-video/talent-1/', response.data['presentation_video'])
        self.assertIn('comunicacao', response.data['presentation_video'])  # testando slugify
        self.assertIn('.mp4', response.data['presentation_video'])
        self.assertIn('avatar/user-1/', response.data['avatar'])
        self.assertIn('comunicacao', response.data['avatar'])  # testando slugify
        self.assertIn('.jpg', response.data['avatar'])

        data['user_id'] = self.user.id
        data['presentation_video'] = response.data['presentation_video']
        data['avatar'] = response.data['avatar']
        data['price'] = '150.00'
        self.refresh_models_from_db()
        self.assertEqual(response.data, data)
        self.assertEqual(self.user.first_name, data['first_name'])
        self.assertEqual(self.user.last_name, data['last_name'])
        self.assertEqual(self.talent.phone_number, data['phone_number'])
        self.assertEqual(self.talent.area_code, data['area_code'])
        self.assertEqual(self.talent.main_social_media, data['main_social_media'])
        self.assertEqual(self.talent.social_media_username, data['social_media_username'])
        self.assertEqual(self.talent.number_of_followers, data['number_of_followers'])
        self.assertEqual(self.customer.phone_number, data['phone_number'])
        self.assertEqual(self.customer.area_code, data['area_code'])

    def test_image_field_is_required_when_there_are_no_image_uploaded_yet(self):
        data = {
            'email': 'talent1@viggio.com.br',
            'first_name': 'Novo Nome',
            'last_name': '',
            'avatar': '',
            'price': 150,
            'description': 'Uma descrição boladona.',
            'available': True,
            'area_code': 12,
            'phone_number': 987654321,
            'main_social_media': 'Instagram',
            'social_media_username': 'talent1',
            'number_of_followers': 1000,
            'presentation_video': SimpleUploadedFile('file.mp4', b'filecontentstring'),
        }
        response = self.client.put(reverse('talents:update'), data=data, format='multipart')
        error_detail = response.data['avatar'][0]
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(error_detail), 'No file was submitted.')
        self.assertEqual(error_detail.code, 'required')

    def test_image_field_is_not_required_when_already_there_are_image_uploaded(self):
        self.customer.avatar = SimpleUploadedFile('my-avatar.jpg', b'filecontentstring')
        self.customer.save()
        data = {
            'email': 'talent1@viggio.com.br',
            'first_name': 'Novo Nome',
            'last_name': '',
            'avatar': '',
            'price': 150,
            'description': 'Uma descrição boladona.',
            'available': True,
            'area_code': 12,
            'phone_number': 987654321,
            'main_social_media': 'Instagram',
            'social_media_username': 'talent1',
            'number_of_followers': 1000,
        }
        response = self.client.put(reverse('talents:update'), data=data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('avatar/user-1/', response.data['avatar'])
        self.assertIn('my-avatar', response.data['avatar'])
        self.assertIn('.jpg', response.data['avatar'])

    def test_presentation_video_can_be_an_empty_string(self):
        data = {
            'email': 'talent1@viggio.com.br',
            'first_name': 'Novo Nome',
            'last_name': '',
            'presentation_video': '',
            'avatar': '',
            'price': 150,
            'description': 'Uma descrição boladona.',
            'available': True,
            'area_code': 12,
            'phone_number': 987654321,
            'main_social_media': 'Instagram',
            'social_media_username': 'talent1',
            'number_of_followers': 1000,
        }
        image_tmp_file = tempfile.NamedTemporaryFile(prefix='my_avatar', suffix='.jpg')
        image = Image.new('RGB', (100, 100))
        image.save(image_tmp_file)
        with open(image_tmp_file.name, 'rb') as avatar:
            data['avatar'] = avatar
            response = self.client.put(reverse('talents:update'), data=data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['presentation_video'])

    def test_send_presentation_video_field_empty_should_not_erase_already_uploaded_video(self):
        PresentationVideo.objects.create(
            talent=self.talent,
            file=SimpleUploadedFile('my-presentation-video.mp4', b'filecontentstring'),
        )
        data = {
            'email': 'talent1@viggio.com.br',
            'first_name': 'Novo Nome',
            'last_name': '',
            'presentation_video': '',
            'avatar': '',
            'price': 150,
            'description': 'Uma descrição boladona.',
            'available': True,
            'area_code': 12,
            'phone_number': 987654321,
            'main_social_media': 'Instagram',
            'social_media_username': 'talent1',
            'number_of_followers': 1000,
        }
        image_tmp_file = tempfile.NamedTemporaryFile(prefix='my_avatar', suffix='.jpg')
        image = Image.new('RGB', (100, 100))
        image.save(image_tmp_file)
        with open(image_tmp_file.name, 'rb') as avatar:
            data['avatar'] = avatar
            response = self.client.put(reverse('talents:update'), data=data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('presentation-video/talent-1/', response.data['presentation_video'])
        self.assertIn('my-presentation-video', response.data['presentation_video'])
        self.assertIn('.mp4', response.data['presentation_video'])

    def test_updating_talent_attaching_new_categories(self):
        data = {
            'email': 'talent1@viggio.com.br',
            'first_name': 'Novo Nome',
            'last_name': '',
            'presentation_video': '',
            'avatar': '',
            'price': 150,
            'description': 'Uma descrição boladona.',
            'available': True,
            'area_code': 12,
            'phone_number': 987654321,
            'main_social_media': 'Instagram',
            'social_media_username': 'talent1',
            'number_of_followers': 1000,
            'categories': [self.category_1.slug, self.category_2.slug]
        }
        image_tmp_file = tempfile.NamedTemporaryFile(prefix='my_avatar', suffix='.jpg')
        image = Image.new('RGB', (100, 100))
        image.save(image_tmp_file)
        with open(image_tmp_file.name, 'rb') as avatar:
            data['avatar'] = avatar
            response = self.client.put(reverse('talents:update'), data=data, format='multipart')
            avatar.seek(0)
        data['categories'] = [
            {'name': self.category_1.name, 'slug': self.category_1.slug},
            {'name': self.category_2.name, 'slug': self.category_2.slug},
        ]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['categories'], data['categories'])
        self.assertEqual(self.talent.categories.count(), 2)

    def test_updating_talent_attaching_a_category_to_categories_set(self):
        self.talent.categories.add(self.category_1, self.category_2)
        data = {
            'email': 'talent1@viggio.com.br',
            'first_name': 'Novo Nome',
            'last_name': '',
            'presentation_video': '',
            'avatar': '',
            'price': 150,
            'description': 'Uma descrição boladona.',
            'available': True,
            'area_code': 12,
            'phone_number': 987654321,
            'main_social_media': 'Instagram',
            'social_media_username': 'talent1',
            'number_of_followers': 1000,
            'categories': [self.category_1.slug, self.category_2.slug, self.category_3.slug]
        }
        image_tmp_file = tempfile.NamedTemporaryFile(prefix='my_avatar', suffix='.jpg')
        image = Image.new('RGB', (100, 100))
        image.save(image_tmp_file)
        with open(image_tmp_file.name, 'rb') as avatar:
            data['avatar'] = avatar
            response = self.client.put(reverse('talents:update'), data=data, format='multipart')
            avatar.seek(0)
        data['categories'] = [
            {'name': self.category_1.name, 'slug': self.category_1.slug},
            {'name': self.category_2.name, 'slug': self.category_2.slug},
            {'name': self.category_3.name, 'slug': self.category_3.slug},
        ]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['categories'], data['categories'])
        self.assertEqual(self.talent.categories.count(), 3)

    def test_updating_talent_removing_some_category_from_categories_set(self):
        self.talent.categories.add(self.category_1, self.category_2, self.category_3)
        data = {
            'email': 'talent1@viggio.com.br',
            'first_name': 'Novo Nome',
            'last_name': '',
            'presentation_video': '',
            'avatar': '',
            'price': 150,
            'description': 'Uma descrição boladona.',
            'available': True,
            'area_code': 12,
            'phone_number': 987654321,
            'main_social_media': 'Instagram',
            'social_media_username': 'talent1',
            'number_of_followers': 1000,
            'categories': [self.category_1.slug, self.category_3.slug]
        }
        image_tmp_file = tempfile.NamedTemporaryFile(prefix='my_avatar', suffix='.jpg')
        image = Image.new('RGB', (100, 100))
        image.save(image_tmp_file)
        with open(image_tmp_file.name, 'rb') as avatar:
            data['avatar'] = avatar
            response = self.client.put(reverse('talents:update'), data=data, format='multipart')
            avatar.seek(0)
        data['categories'] = [
            {'name': self.category_1.name, 'slug': self.category_1.slug},
            {'name': self.category_3.name, 'slug': self.category_3.slug},
        ]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['categories'], data['categories'])
        self.assertEqual(self.talent.categories.count(), 2)

    def test_updating_talent_removing_all_categories_when_field_is_empty(self):
        self.talent.categories.add(self.category_1, self.category_2, self.category_3)
        data = {
            'email': 'talent1@viggio.com.br',
            'first_name': 'Novo Nome',
            'last_name': '',
            'presentation_video': '',
            'avatar': '',
            'price': 150,
            'description': 'Uma descrição boladona.',
            'available': True,
            'area_code': 12,
            'phone_number': 987654321,
            'main_social_media': 'Instagram',
            'social_media_username': 'talent1',
            'number_of_followers': 1000,
            'categories': [],
        }
        image_tmp_file = tempfile.NamedTemporaryFile(prefix='my_avatar', suffix='.jpg')
        image = Image.new('RGB', (100, 100))
        image.save(image_tmp_file)
        with open(image_tmp_file.name, 'rb') as avatar:
            data['avatar'] = avatar
            response = self.client.put(reverse('talents:update'), data=data, format='multipart')
            avatar.seek(0)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['categories'], data['categories'])
        self.assertEqual(self.talent.categories.count(), 0)

    def test_updating_talent_removing_all_categories_when_field_is_missing(self):
        self.talent.categories.add(self.category_1, self.category_2, self.category_3)
        data = {
            'email': 'talent1@viggio.com.br',
            'first_name': 'Novo Nome',
            'last_name': '',
            'presentation_video': '',
            'avatar': '',
            'price': 150,
            'description': 'Uma descrição boladona.',
            'available': True,
            'area_code': 12,
            'phone_number': 987654321,
            'main_social_media': 'Instagram',
            'social_media_username': 'talent1',
            'number_of_followers': 1000,
        }
        image_tmp_file = tempfile.NamedTemporaryFile(prefix='my_avatar', suffix='.jpg')
        image = Image.new('RGB', (100, 100))
        image.save(image_tmp_file)
        with open(image_tmp_file.name, 'rb') as avatar:
            data['avatar'] = avatar
            response = self.client.put(reverse('talents:update'), data=data, format='multipart')
            avatar.seek(0)
        data['categories'] = []
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['categories'], data['categories'])
        self.assertEqual(self.talent.categories.count(), 0)


class RetrieveTalentTest(APITestCase):

    def setUp(self):
        user = User.objects.create(
            email='talent1@viggio.com.br',
            first_name='Nome',
            last_name='Sobrenome',
        )
        customer = Customer.objects.create(
            user=user,
            avatar=SimpleUploadedFile('avatar.jpg', b'filecontentstring'),
        )
        self.talent = Talent.objects.create(
            user=user,
            phone_number=1,
            area_code=1,
            main_social_media='',
            social_media_username='',
            number_of_followers=1,
            price=100,
        )
        presentation_video = PresentationVideo.objects.create(
            talent=self.talent,
            file=SimpleUploadedFile('file.mp4', b'filecontentstring'),
        )
        self.expected_response_data = {
            'talent_id': 1,
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'presentation_video': presentation_video.file.url,
            'avatar': customer.avatar.url,
            'price': '100.00',
            'description': '',
            'available': False,
            'categories': [],
        }
        self.category_1 = Category.objects.create(name='Youtubers', slug='youtubers')
        self.category_2 = Category.objects.create(name='Influencers', slug='influencers')

    def test_retrieving_talent_detail(self):
        response = self.client.get(
            reverse('talents:retrieve', kwargs={'talent_id': self.talent.id}),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), self.expected_response_data)

    def test_retriving_talent_detail_with_categories(self):
        self.talent.categories.add(self.category_1, self.category_2)
        self.expected_response_data.update({
            'categories': [
                {
                    'name': self.category_1.name,
                    'slug': self.category_1.slug,
                },
                {
                    'name': self.category_2.name,
                    'slug': self.category_2.slug,
                },
            ]
        })
        response = self.client.get(
            reverse('talents:retrieve', kwargs={'talent_id': self.talent.id}),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), self.expected_response_data)


class TalentListTest(APITestCase):

    def setUp(self):
        self.user1 = User(
            email='talent1@viggio.com.br',
            first_name='Nome',
            last_name='Sobrenome',
        )
        self.user1.save()
        self.customer1 = Customer.objects.create(user=self.user1)
        self.talent1 = Talent.objects.create(
            user=self.user1,
            phone_number=1,
            area_code=1,
            main_social_media='',
            social_media_username='',
            number_of_followers=1,
            available=True,
            description='some description',
        )
        self.user2 = User(
            email='talent2@viggio.com.br',
            first_name='Nome',
            last_name='Sobrenome',
        )
        self.user2.save()
        self.customer2 = Customer.objects.create(user=self.user2)
        self.talent2 = Talent.objects.create(
            user=self.user2,
            phone_number=1,
            area_code=1,
            main_social_media='',
            social_media_username='',
            number_of_followers=1,
            available=True,
            description='some description',
        )
        self.category_1 = Category.objects.create(name='Youtubers', slug='youtubers')
        self.category_2 = Category.objects.create(name='Influencers', slug='influencers')
        self.talent1.categories.add(self.category_1, self.category_2)
        self.talent2.categories.add(self.category_2)

    def test_listing(self):
        talent_1_data = {
            'talent_id': 1,
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'price': None,
            'presentation_video': None,
            'avatar': None,
            'available': True,
            'description': 'some description',
            'categories': [
                {
                    'name': self.category_1.name,
                    'slug': self.category_1.slug,
                },
                {
                    'name': self.category_2.name,
                    'slug': self.category_2.slug,
                }
            ]
        }
        talent_2_data = {
            'talent_id': 2,
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'price': None,
            'presentation_video': None,
            'avatar': None,
            'available': True,
            'description': 'some description',
            'categories': [
                {
                    'name': 'Influencers',
                    'slug': 'influencers',
                }
            ]
        }
        response = self.client.get(reverse('talents:list'), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(talent_1_data, response.data)
        self.assertIn(talent_2_data, response.data)


@override_settings(
    task_eager_propagates=True,
    task_always_eager=True,
    broker_url='memory://',
    backend='memory'
)
class TalentEnrollmentTest(APITestCase):

    @mock.patch('post_office.mailgun.requests')
    def test_notify_staff_about_new_talent_enrollment(self, mocked_requests):
        talent_data = {
            'email': 'talento@youtuber.com',
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'phone_number': '123456789',
            'area_code': '11',
            'main_social_media': 'Youtube',
            'social_media_username': 'nome_sobrenome',
            'number_of_followers': 1000,
        }
        expected_calls = [
            mock.call(
                auth=('api', os.environ['MAILGUN_API_KEY']),
                url=os.environ['MAILGUN_API_URL'],
                data={
                    'from': os.environ['CONTACT_EMAIL'],
                    'to': os.environ['STAFF_EMAIL'].split(','),
                    'subject': 'Pedido de inscrição de talento',
                    'template': 'notify-staff-about-new-talent-enrollment',
                    'v:email': talent_data['email'],
                    'v:first_name': talent_data['first_name'],
                    'v:last_name': talent_data['last_name'],
                    'v:phone_number': talent_data['phone_number'],
                    'v:area_code': talent_data['area_code'],
                    'v:main_social_media': talent_data['main_social_media'],
                    'v:social_media_username': talent_data['social_media_username'],
                    'v:number_of_followers': talent_data['number_of_followers'],
                },
            ),
        ]
        response = self.client.post(reverse('talents:enroll'), talent_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(mocked_requests.post.mock_calls, expected_calls)


class TalentShoutoutListTest(APITestCase):

    def setUp(self):
        user = User.objects.create(
            email='talent@youtuber.com',
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
        self.order_1 = Order.objects.create(
            hash_id=ORDER_1_HASH,
            talent=self.talent,
            video_is_for='someone_else',
            is_from='MJ',
            is_to='Peter',
            instruction="Go Get 'em, Tiger",
            email='customer1@buyer.com',
            is_public=True,
            expiration_datetime=self.tomorrow,
        )
        Charge.objects.create(
            order=self.order_1,
            amount_paid=150,
            payment_date=self.tomorrow,
            payment_method='credit_card',
            status=DomainCharge.PAID,
        )
        self.shoutout_1 = ShoutoutVideo.objects.create(
            hash_id=SHOUTOUT_1_HASH,
            order=self.order_1,
            talent=self.talent,
            file=SimpleUploadedFile('file.mp4', b'filecontentstring'),
        )
        self.order_2 = Order.objects.create(
            hash_id=ORDER_2_HASH,
            talent=self.talent,
            video_is_for='someone_else',
            is_from='MJ',
            is_to='Peter',
            instruction="Go Get 'em, Tiger",
            email='customer2@buyer.com',
            is_public=True,
            expiration_datetime=self.tomorrow,
        )
        Charge.objects.create(
            order=self.order_2,
            amount_paid=150,
            payment_date=self.tomorrow,
            payment_method='credit_card',
            status=DomainCharge.PAID,
        )
        self.shoutout_2 = ShoutoutVideo.objects.create(
            hash_id=SHOUTOUT_2_HASH,
            order=self.order_2,
            talent=self.talent,
            file=SimpleUploadedFile('file.mp4', b'filecontentstring'),
        )
        user_2 = User.objects.create(
            email='talent_2@youtuber.com',
            first_name='Nome',
            last_name='Sobrenome',
        )
        self.talent_2 = Talent.objects.create(
            user=user_2,
            phone_number=1,
            area_code=1,
            main_social_media='',
            social_media_username='',
            number_of_followers=1,
        )

    def test_retrieving_shoutouts_by_talent(self):
        expected_shoutouts_data = [
            {
                'shoutout_hash': str(SHOUTOUT_1_HASH),
                'file': f'http://testserver{self.shoutout_1.file.url}',
            },
            {
                'shoutout_hash': str(SHOUTOUT_2_HASH),
                'file': f'http://testserver{self.shoutout_2.file.url}',
            },
        ]
        response = self.client.get(
            reverse('talents:shoutouts', kwargs={'talent_id': self.talent.id}),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected_shoutouts_data)

    def test_when_talent_have_no_shoutouts(self):
        response = self.client.get(
            reverse('talents:shoutouts', kwargs={'talent_id': self.talent_2.id}),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])
