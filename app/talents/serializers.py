from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import serializers

from categories.models import Category
from categories.serializers import CategorySerializer
from customers.models import Customer
from shoutouts.models import ShoutoutVideo
from .models import Talent, PresentationVideo


User = get_user_model()


class EnrollSerializer(serializers.ModelSerializer):
    email = serializers.CharField(max_length=100)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)

    class Meta:
        model = Talent
        fields = [
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'area_code',
            'main_social_media',
            'social_media_username',
            'number_of_followers',
        ]

    def create(self, validated_data):
        if User.objects.filter(email=validated_data['email']).exists():
            return validated_data
        user = User(
            username=validated_data['email'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            is_active=False,
        )
        user.set_password('123@mudar')
        user.save()
        Talent.objects.create(
            user=user,
            phone_number=validated_data['phone_number'],
            area_code=validated_data['area_code'],
            main_social_media=validated_data['main_social_media'],
            social_media_username=validated_data['social_media_username'],
            number_of_followers=validated_data['number_of_followers'],
        )
        Customer.objects.create(
            user=user,
            phone_number=validated_data['phone_number'],
            area_code=validated_data['area_code'],
        )
        return validated_data


class TalentInfoSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    email = serializers.CharField()
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100, allow_blank=True)
    avatar = serializers.ImageField(required=False)
    presentation_video = serializers.FileField(required=False)
    categories = CategorySerializer(many=True, required=False)

    class Meta:
        model = Talent
        fields = [
            'user_id',
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'area_code',
            'main_social_media',
            'social_media_username',
            'number_of_followers',
            'price',
            'description',
            'presentation_video',
            'available',
            'avatar',
            'categories'
        ]

    def __init__(self, *args, **kwargs):
        instance = args[0]
        instance.email = instance.user.email
        instance.user_id = instance.user.id
        instance.first_name = instance.user.first_name
        instance.last_name = instance.user.last_name
        instance.avatar = instance.user.customer.avatar
        instance.categories_data = None
        if 'data' in kwargs:
            data = dict(kwargs['data'])
            categories_data = data.get('categories')
            instance.categories_data = categories_data
        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        reprensetation = super().to_representation(instance)
        if hasattr(instance, 'presentation_video'):
            reprensetation['presentation_video'] = instance.presentation_video.file.url
        if instance.user.customer.avatar:
            reprensetation['avatar'] = instance.user.customer.avatar.url
        return reprensetation

    def _update_user(self, email, validated_data):
        user_queryset = User.objects.filter(email=email)
        user_queryset.update(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )

    def _update_presentation_video(self, instance, uploaded_presentation_video):
        defaults = {'file': uploaded_presentation_video}
        PresentationVideo.objects.update_or_create(talent=instance, defaults=defaults)

    def _update_talent(self, email, validated_data):
        talent_queryset = Talent.objects.filter(user__email=email)
        talent_queryset.update(
            phone_number=validated_data['phone_number'],
            area_code=validated_data['area_code'],
            main_social_media=validated_data['main_social_media'],
            social_media_username=validated_data['social_media_username'],
            number_of_followers=validated_data['number_of_followers'],
            price=validated_data['price'],
            description=validated_data['description'],
            available=validated_data['available'],
        )

    def _update_customer(self, email, validated_data):
        defaults = {
            'avatar': validated_data['avatar'],
            'phone_number': validated_data['phone_number'],
            'area_code': validated_data['area_code'],
        }
        Customer.objects.update_or_create(user__email=email, defaults=defaults)

    def _update_categories(self, instance):
        instance.categories.clear()
        if instance.categories_data:
            categories = Category.objects.filter(slug__in=instance.categories_data)
            instance.categories.set(categories)

    def _validate_avatar_field(self, validated_data, instance):
        if not validated_data.get('avatar'):
            if instance.user.customer.avatar:
                validated_data['avatar'] = instance.user.customer.avatar
            else:
                error = {'avatar': ['No file was submitted.']}
                raise serializers.ValidationError(error, code='required')

    def update(self, instance, validated_data):
        email = instance.user.email
        if not instance.email == validated_data['email']:
            raise Exception("Não é possível alterar o endereço de email")
        with transaction.atomic():
            uploaded_presentation_video = validated_data.get('presentation_video')
            if uploaded_presentation_video:
                self._update_presentation_video(instance, uploaded_presentation_video)
            self._update_user(email, validated_data)
            self._update_talent(email, validated_data)
            self._validate_avatar_field(validated_data, instance)
            self._update_customer(email, validated_data)
            self._update_categories(instance)
        instance.refresh_from_db()
        instance.first_name = validated_data['first_name']
        instance.last_name = validated_data['last_name']
        return instance


class TalentDetailSerializer(serializers.ModelSerializer):
    talent_id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField(allow_null=True)
    avatar = serializers.ImageField(allow_null=True)
    categories = CategorySerializer(many=True, required=False)

    class Meta:
        model = Talent
        fields = [
            'talent_id',
            'first_name',
            'last_name',
            'price',
            'description',
            'presentation_video',
            'avatar',
            'available',
            'categories',
        ]

    def to_representation(self, instance):
        instance.avatar = instance.user.customer.avatar
        instance.talent_id = instance.id
        instance.first_name = instance.user.first_name
        instance.last_name = instance.user.last_name
        reprensetation = super().to_representation(instance)
        if hasattr(instance, 'presentation_video'):
            reprensetation['presentation_video'] = instance.presentation_video.file.url
        if instance.user.customer.avatar:
            reprensetation['avatar'] = instance.user.customer.avatar.url
        return reprensetation


class ShoutoutSerializer(serializers.ModelSerializer):
    shoutout_hash = serializers.UUIDField(read_only=True)

    class Meta:
        model = ShoutoutVideo
        fields = ['shoutout_hash', 'file']

    def to_representation(self, instance):
        reprensetation = super().to_representation(instance)
        reprensetation['shoutout_hash'] = instance.hash_id
        return reprensetation
