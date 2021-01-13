import uuid
from django.conf import settings
from django.db import models
from django.utils.text import slugify
from orders.models import Order
from talents.models import Talent
from utils.base_models import BaseModel
from transcoder.transcoders import TRANSCODED_VIDEO_GENERIC_NAME


def upload_location(instance, filename):
    extension = filename.split('.')[-1]
    talent = instance.order.talent
    is_to_slug = slugify(instance.order.is_to)
    orders_directory = f'{settings.MEDIA_DIRECTORY}/orders/'
    order_unique_identifier = f'talent-{talent.id}/order-{instance.order.hash_id}/'
    new_filename = f'viggio-para-{is_to_slug}.{extension}'
    if TRANSCODED_VIDEO_GENERIC_NAME in filename:
        new_filename = f'{extension}/viggio-para-{is_to_slug}.{extension}'
    return orders_directory + order_unique_identifier + new_filename


class ShoutoutVideo(BaseModel):
    hash_id = models.UUIDField(unique=True, default=uuid.uuid4)
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        unique=True,
        related_name='shoutout',
    )
    talent = models.ForeignKey(Talent, on_delete=models.CASCADE)
    file = models.FileField(upload_to=upload_location, max_length=140)

    def __str__(self):
        return f'customer: {self.order.email} - talent: {self.order.talent}'

    @classmethod
    def persist(cls, domain_shoutout):
        shoutout = cls.objects.create(
            hash_id=domain_shoutout.hash_id,
            order_id=domain_shoutout.order_id,
            talent_id=domain_shoutout.talent_id,
            file=domain_shoutout.video_file,
        )
        domain_shoutout.video_file = shoutout.file
