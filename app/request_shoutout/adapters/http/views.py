import uuid
from distutils.util import strtobool

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from message_bus.routes import (
    get_charge_order_bus,
    get_fulfill_shoutout_request_bus,
)
from request_shoutout.adapters.db.orm import (
    PersistingShoutoutRequestError,
    PersistingShoutoutVideoError,
    ChargingShoutoutRequestError,
)
from request_shoutout.domain.messages import FulfillShoutoutRequestCommand, RequestShoutoutCommand
from request_shoutout.domain.models import (
    OrderHasShoutoutError,
    OrderExpiredError,
    TalentPermissionError,
)
from talents.models import Talent
from talents.permissions import TalentAccessPermission


class ChargeOrderAPIView(APIView):
    http_method_names = ['post']

    def _set_is_public_field(self, request):
        request.data['order_is_public'] = not request.data['order_is_not_public']
        request.data.pop('order_is_not_public')

    def _replicate_buyer_data(self, request):
        request.data['credit_card_owner_birthdate'] = request.data['customer_birthdate']
        request.data['credit_card_owner_area_code'] = request.data['customer_area_code']
        request.data['credit_card_owner_phone_number'] = request.data['customer_phone_number']
        request.data['credit_card_owner_tax_document'] = request.data['customer_tax_document']

    def post(self, request, *args, **kwargs):
        hash_id = uuid.uuid4()
        self._set_is_public_field(request)
        is_buyer_credit_card_owner = not bool(strtobool(request.data['not_my_cc']))
        if is_buyer_credit_card_owner:
            self._replicate_buyer_data(request)
        request.data.pop('not_my_cc')
        command = RequestShoutoutCommand(order_hash_id=hash_id, **request.data)
        bus = get_charge_order_bus()
        try:
            bus.handle(command)
        except ChargingShoutoutRequestError:
            return Response(
                {'error': 'An issue happened while processing payment.'},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except PersistingShoutoutRequestError:
            return Response(
                {'error': 'An issue happened while persisting data.'},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response({'order_hash': hash_id}, status.HTTP_201_CREATED)


class FulfillShoutoutRequestAPIView(APIView):
    permission_classes = (IsAuthenticated, TalentAccessPermission)
    http_method_names = ['post']
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def post(self, request, *args, **kwargs):
        hash_id = uuid.uuid4()
        talent = Talent.objects.get(user_id=request.user.id)
        command = FulfillShoutoutRequestCommand(
            shoutout_hash=hash_id,
            order_hash=request.data['order_hash'],
            video_file=request.data['order_video'],
            talent_id=talent.id,
        )
        bus = get_fulfill_shoutout_request_bus()
        try:
            bus.handle(command)
        except PersistingShoutoutVideoError:
            return Response(
                {'error': 'It happened an issue when persisting shoutout video'},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except OrderHasShoutoutError:
            return Response(
                {'error': 'Order already has a shoutout attached.'},
                status.HTTP_400_BAD_REQUEST,
            )
        except OrderExpiredError:
            return Response(
                {'error': "Can't fulfill an expired order."},
                status.HTTP_400_BAD_REQUEST,
            )
        except TalentPermissionError:
            return Response(
                {'error': 'Order belongs to another Talent.'},
                status.HTTP_400_BAD_REQUEST,
            )
        return Response({'shoutout_hash': hash_id}, status.HTTP_201_CREATED)
