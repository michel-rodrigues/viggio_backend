from rest_framework import serializers

from orders.models import Charge, Order


class ChargeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Charge
        fields = [
            'amount_paid',
            'payment_date',
            'payment_method',
            'status',
        ]


class OrderSerializer(serializers.ModelSerializer):
    order_hash = serializers.UUIDField(read_only=True)
    shoutout_hash = serializers.UUIDField(read_only=True)
    charge = ChargeSerializer()

    class Meta:
        model = Order
        fields = [
            'order_hash',
            'talent_id',
            'video_is_for',
            'is_from',
            'is_to',
            'instruction',
            'email',
            'expiration_datetime',
            'is_public',
            'shoutout_hash',
            'charge',
        ]

    def to_representation(self, instance):
        reprensetation = super().to_representation(instance)
        reprensetation['order_hash'] = instance.hash_id
        if hasattr(instance, 'shoutout'):
            reprensetation['shoutout_hash'] = instance.shoutout.hash_id
        return reprensetation
