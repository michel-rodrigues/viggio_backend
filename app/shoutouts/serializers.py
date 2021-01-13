from rest_framework import serializers

from orders.serializers import OrderSerializer

from .models import ShoutoutVideo


class ShoutoutSerializer(serializers.ModelSerializer):
    order = OrderSerializer()
    shoutout_hash = serializers.UUIDField(read_only=True)

    class Meta:
        model = ShoutoutVideo
        fields = [
            'shoutout_hash',
            'talent_id',
            'file',
            'order',
        ]

    def to_representation(self, instance):
        reprensetation = super().to_representation(instance)
        reprensetation['shoutout_hash'] = instance.hash_id
        return reprensetation
