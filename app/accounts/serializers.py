from django.contrib.auth import get_user_model

from rest_framework import serializers

from customers.models import Customer
from .tokens import get_new_tokens


User = get_user_model()


class UserCreateSerializer(serializers.ModelSerializer):
    access = serializers.CharField(allow_blank=True, read_only=True)
    refresh = serializers.CharField(allow_blank=True, read_only=True)
    user_type = serializers.CharField(allow_blank=True, read_only=True)
    user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            'email',
            'password',
            'first_name',
            'last_name',
            'user_id',
            'access',
            'refresh',
            'user_type',
        ]
        extra_kwargs = {
            # Faz com que a senha não seja incluída no JSON retornado para exibição
            'password': {
                'write_only': True,
            },
            'email': {
                'required': True,
            },
            'first_name': {
                'required': True,
                'allow_blank': False,
            },
            'last_name': {
                'required': True,
                'allow_blank': False,
            }
        }

    def validate(self, data):
        validated_data = super().validate(data)
        if User.objects.filter(email=validated_data['email']).exists():
            raise serializers.ValidationError(
                {'message': 'Esse endereço de email já está registrado.'}
            )
        return validated_data

    def create(self, validated_data):
        user = User(
            username=validated_data['email'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        Customer.objects.create(user=user)
        access, refresh = get_new_tokens(user)
        validated_data.update({
            'access': access,
            'refresh': refresh,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_id': user.id,
            'user_type': user.is_talent,
        })
        return validated_data


class UserLoginSerializer(serializers.ModelSerializer):
    access = serializers.CharField(allow_blank=True, read_only=True)
    refresh = serializers.CharField(allow_blank=True, read_only=True)
    user_type = serializers.CharField(allow_blank=True, read_only=True)
    user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            'email',
            'password',
            'first_name',
            'last_name',
            'user_id',
            'access',
            'refresh',
            'user_type',
        ]
        extra_kwargs = {
            # Faz com que a senha não incluida no JSON retornado para exibição
            'password': {
                'write_only': True,
            },
            'email': {
                'required': True,
            },
            'first_name': {
                'allow_blank': True,
                'read_only': True,
            },
            'last_name': {
                'allow_blank': True,
                'read_only': True,
            }
        }

    def validate(self, data):
        email = data['email']
        password = data['password']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({'message': 'Email ou senha inválidos.'})
        if user and not user.check_password(password):
            raise serializers.ValidationError({'message': 'Email ou senha inválidos.'})
        access, refresh = get_new_tokens(user)
        data.update({
            'access': access,
            'refresh': refresh,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_id': user.id,
            'user_type': user.is_talent
        })
        return data
