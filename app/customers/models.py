from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import slugify

from utils.base_models import BaseModel


User = get_user_model()


def upload_location(instance, filename):
    extension = filename.split('.')[-1]
    name = slugify(''.join((filename.split('.')[:-1])))
    return f'avatar/user-{instance.user.id}/{name}.{extension}'


class Customer(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to=upload_location, max_length=100, null=True)
    phone_number = models.CharField(max_length=9, blank=True)
    area_code = models.CharField(max_length=2, blank=True)
    mailing_list = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.email}'
