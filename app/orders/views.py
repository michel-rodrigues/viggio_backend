from datetime import datetime, timezone

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from request_shoutout.domain.models import Charge as DomainCharge
from talents.permissions import TalentAccessPermission
from .serializers import OrderSerializer


class TalentOrdersAPIView(ListAPIView):
    permission_classes = (IsAuthenticated, TalentAccessPermission)
    serializer_class = OrderSerializer

    def get_queryset(self):
        talent = self.request.user.talent
        orders_with_pre_authorized_payment = Order.objects.filter(
            talent=talent,
            charge__status=DomainCharge.PRE_AUTHORIZED,
            expiration_datetime__gt=datetime.now(timezone.utc),
            shoutout__isnull=True,
        )
        return orders_with_pre_authorized_payment.order_by('expiration_datetime')


class OrderDetailAPIView(APIView):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        order_hash = kwargs['order_hash']
        order = get_object_or_404(Order, hash_id=order_hash)
        serialized = OrderSerializer(order)
        return Response(serialized.data, status.HTTP_200_OK)
