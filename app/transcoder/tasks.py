from celery.exceptions import TimeLimitExceeded

from project_configuration.celery import app
from request_shoutout.domain.messages import ShoutoutSuccessfullyTranscodedEvent
from shoutouts.models import ShoutoutVideo
from .transcoders import transcode, TranscodeError


def to_mp4(shoutout_hash_id):
    schedule_transcode_to_mp4.delay(shoutout_hash_id)


@app.task(max_retries=10, autoretry_for=(TranscodeError, TimeLimitExceeded))
def schedule_transcode_to_mp4(shoutout_hash_id):
    from message_bus.routes import get_fulfill_shoutout_request_bus
    shoutout = ShoutoutVideo.objects.get(hash_id=shoutout_hash_id)
    transcode(shoutout, 'mp4')
    event = ShoutoutSuccessfullyTranscodedEvent(shoutout.order_id)
    bus = get_fulfill_shoutout_request_bus()
    bus.handle(event)
