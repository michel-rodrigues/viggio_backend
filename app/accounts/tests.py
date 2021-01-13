import os
from unittest import mock

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from customers.models import Customer
from talents.models import Talent


User = get_user_model()


class SignUpTest(APITestCase):

    def test_making_signup_create_a_customer(self):
        data = {
            'email': 'teste@viggio.com.br',
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'password': 'senha123',
        }
        response = self.client.post(reverse('accounts:signup'), data, format='json')
        user = User.objects.get(email=data['email'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], data['email'])
        self.assertEqual(response.data['first_name'], data['first_name'])
        self.assertEqual(response.data['last_name'], data['last_name'])
        self.assertEqual(response.data['user_id'], user.id)
        self.assertNotIn('password', response.data)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(data['email'], user.email)
        self.assertEqual(data['last_name'], user.last_name)
        self.assertEqual(data['first_name'], user.first_name, )
        self.assertEqual(response.data['user_type'], 'customer')
        self.assertTrue(Customer.objects.filter(user=user).exists())

    def test_wrong_email_pattern(self):
        data = {
            'email': 'teste@viggio',
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'password': 'senha123',
        }
        response = self.client.post(reverse('accounts:signup'), data, format='json')
        validation_error = response.data['email'][0]
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(validation_error, 'Enter a valid email address.')

    def test_lacking_email(self):
        data = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'password': 'senha123',
        }
        response = self.client.post(reverse('accounts:signup'), data, format='json')
        validation_error = response.data['email'][0]
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(validation_error, 'This field is required.')

    def test_lacking_password(self):
        data = {
            'email': 'customer@viggio.com.br',
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
        }
        response = self.client.post(reverse('accounts:signup'), data, format='json')
        validation_error = response.data['password'][0]
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(validation_error, 'This field is required.')

    def test_lacking_first_name(self):
        data = {
            'email': 'customer@viggio.com.br',
            'last_name': 'Sobrenome',
            'password': 'senha123',
        }
        response = self.client.post(reverse('accounts:signup'), data, format='json')
        validation_error = response.data['first_name'][0]
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(validation_error, 'This field is required.')

    def test_lacking_last_name(self):
        data = {
            'email': 'customer@viggio.com.br',
            'first_name': 'Nome',
            'password': 'senha123',
        }
        response = self.client.post(reverse('accounts:signup'), data, format='json')
        validation_error = response.data['last_name'][0]
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(validation_error, 'This field is required.')


class SignInTest(APITestCase):

    def setUp(self):
        self.password = 'senha123'
        self.user = User(
            email='customer@viggio.com.br',
            first_name='Nome',
            last_name='Sobrenome',
        )
        self.user.set_password(self.password)
        self.user.save()

    def test_making_login(self):
        data = {
            'email': self.user.email,
            'password': self.password,
        }
        response = self.client.post(reverse('accounts:signin'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['first_name'], self.user.first_name)
        self.assertEqual(response.data['last_name'], self.user.last_name)
        self.assertEqual(response.data['user_id'], self.user.id)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_making_login_with_customer(self):
        data = {
            'email': self.user.email,
            'password': self.password,
        }
        response = self.client.post(reverse('accounts:signin'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_type'], 'customer')

    def test_making_login_with_talent(self):
        Talent.objects.create(
            user=self.user,
            phone_number=0,
            area_code=0,
            main_social_media='dummy_data',
            social_media_username='dummy_data',
            number_of_followers=0,
        )
        data = {
            'email': self.user.email,
            'password': self.password,
        }
        response = self.client.post(reverse('accounts:signin'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_type'], 'talent')

    def test_wrong_email(self):
        data = {
            'email': 'wrong_email@viggio.com.br',
            'password': self.password,
        }
        response = self.client.post(reverse('accounts:signin'), data, format='json')
        validation_error = response.data['message'][0]
        expected_msg_error = 'Email ou senha inválidos.'
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(validation_error, expected_msg_error)

    def test_wrong_email_pattern(self):
        data = {
            'email': 'wrong_email@viggio',
            'password': self.password,
        }
        response = self.client.post(reverse('accounts:signin'), data, format='json')
        validation_error = response.data['email'][0]
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(validation_error, 'Enter a valid email address.')

    def test_wrong_password(self):
        data = {
            'email': self.user.email,
            'password': 'wrong_password',
        }
        response = self.client.post(reverse('accounts:signin'), data, format='json')
        validation_error = response.data['message'][0]
        expected_msg_error = 'Email ou senha inválidos.'
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(validation_error, expected_msg_error)

    def test_lacking_email(self):
        data = {'password': self.password}
        response = self.client.post(reverse('accounts:signin'), data, format='json')
        validation_error = response.data['email'][0]
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(validation_error, 'This field is required.')

    def test_lacking_password(self):
        data = {'email': 'wrong_email@viggio.com.br'}
        response = self.client.post(reverse('accounts:signin'), data, format='json')
        validation_error = response.data['password'][0]
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(validation_error, 'This field is required.')


class ChangePasswordTest(APITestCase):

    def do_login(self, user, password):
        data = {
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'password': password,
        }
        response = self.client.post(reverse('accounts:signin'), data, format='json')
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def setUp(self):
        self.password = 'senha123'
        self.user = User.objects.create(
            email='generic@user.com',
            first_name='Nome',
            last_name='Sobrenome',
        )
        self.user.set_password(self.password)
        self.user.save()
        self.new_password = 'supersecretpassword'

    def test_changing_password(self):
        self.do_login(self.user, self.password)
        data = {
            'old_password': self.password,
            'new_password': self.new_password,
            'new_password_confirmation': self.new_password,
        }
        response = self.client.post(reverse('accounts:change_password'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.new_password))
        self.assertTrue(self.user.is_authenticated)
        self.assertIn('refresh', response.data)
        self.assertIn('access', response.data)
        self.assertNotEqual(response.data['access'], self.token)
        self.assertNotIn('password', response.data)
        self.assertEqual(response.data['user_id'], self.user.id)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['last_name'], self.user.last_name)
        self.assertEqual(response.data['first_name'], self.user.first_name, )
        self.assertEqual(response.data['user_type'], 'customer')

    def test_anonymous_user_cant_change_password(self):
        data = {
            'old_password': self.password,
            'new_password': self.new_password,
            'new_password_confirmation': self.new_password,
        }
        response = self.client.post(reverse('accounts:change_password'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_wrong_old_password(self):
        self.do_login(self.user, self.password)
        data = {
            'old_password': '123mudar',
            'new_password': self.new_password,
            'new_password_confirmation': self.new_password,
        }
        response = self.client.post(reverse('accounts:change_password'), data, format='json')
        validation_error = response.data['message'][0]
        expected_msg_error = 'Senha atual ou senha de confirmação errada.'
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(validation_error, expected_msg_error)

    def test_new_password_confirmation_mismatch(self):
        self.do_login(self.user, self.password)
        data = {
            'old_password': self.password,
            'new_password': self.new_password,
            'new_password_confirmation': '123mudar',
        }
        response = self.client.post(reverse('accounts:change_password'), data, format='json')
        validation_error = response.data['message'][0]
        expected_msg_error = 'Senha atual ou senha de confirmação errada.'
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(validation_error, expected_msg_error)


class ResetPasswordTest(APITestCase):

    def setUp(self):
        self.password = 'senha123'
        self.email = 'generic@user.com'
        self.user = User.objects.create(
            email=self.email,
            first_name='Nome',
            last_name='Sobrenome',
        )
        self.user.set_password(self.password)
        self.user.save()

    @mock.patch('post_office.mailgun.requests')
    def test_reset_password(self, mocked_requests):
        data = {'email': self.email}
        response = self.client.post(reverse('accounts:reset_password'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password(self.password))

    @mock.patch('post_office.mailgun.requests')
    def test_provide_email_wich_doesnt_exist(self, mocked_requests):
        data = {'email': 'fake@user.com'}
        response = self.client.post(reverse('accounts:reset_password'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch('accounts.views.random_string_digits', return_value='abc123')
    @mock.patch('post_office.mailgun.requests')
    def test_send_email_with_new_password(self, mocked_requests, mocked_random_string_digits):
        data = {'email': self.email}
        response = self.client.post(reverse('accounts:reset_password'), data, format='json')
        expected_calls = [
            mock.call(
                auth=('api', os.environ['MAILGUN_API_KEY']),
                url=os.environ['MAILGUN_API_URL'],
                data={
                    'from': os.environ['CONTACT_EMAIL'],
                    'to': 'Nome Sobrenome <generic@user.com>',
                    'subject': 'Pedido de nova senha',
                    'template': 'user-new-password',
                    'v:new_password': 'abc123',
                    'v:first_name': self.user.first_name,
                    'v:last_name': self.user.last_name,
                },
            ),
        ]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mocked_requests.post.mock_calls, expected_calls)
