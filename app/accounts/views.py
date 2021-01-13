import os

from django.contrib.auth import get_user_model
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

from post_office.mailgun import sync_mailgun_carrier
from request_shoutout.domain.emails.templates import MailRequest
from request_shoutout.domain.emails.template_builders import user_reset_password_template_builder
from utils.weak_random import random_string_digits
from .serializers import UserCreateSerializer, UserLoginSerializer
from .tokens import get_new_tokens


User = get_user_model()


def change_password(user, password):
    user.set_password(password)
    user.save()


class UserCreateAPIView(CreateAPIView):
    serializer_class = UserCreateSerializer
    queryset = User.objects.all()


class UserLoginAPIView(APIView):
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            return Response(serializer.data)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class ChangePasswordAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    http_method_names = ['post']

    def _is_valid(self, user, data):
        correct_old_password = user.check_password(data['old_password'])
        new_password_is_valid = (
            data['new_password'] == data['new_password_confirmation']
        )
        return correct_old_password and new_password_is_valid

    def post(self, request, *args, **kwargs):
        user = request.user
        if not self._is_valid(user, request.data):
            msg = 'Senha atual ou senha de confirmação errada.'
            return Response({'message': [msg]}, status=HTTP_400_BAD_REQUEST)
        change_password(user, request.data['new_password'])
        access, refresh = get_new_tokens(user)
        response_data = {
            'access': access,
            'refresh': refresh,
            'user_id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_type': user.is_talent,
        }
        return Response(response_data)


class ResetPasswordAPIView(APIView):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        email = request.data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({}, status=HTTP_400_BAD_REQUEST)
        new_password = random_string_digits()
        change_password(user, new_password)
        to_user = MailRequest(
            to_email=f'{user.get_full_name()} <{user.email}>',
            from_email=os.environ['CONTACT_EMAIL'],
            template=user_reset_password_template_builder(
                new_password,
                user.first_name,
                user.last_name,
            ),
        )
        sync_mailgun_carrier(mail_request=to_user)
        return Response({})
