import os

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from sentry_sdk import capture_message

from .tasks import update_payment_status


class WebhookPaymentAPIView(APIView):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        if request.META['HTTP_AUTHORIZATION'] == os.environ['WIRECARD_PAYMENT_WEBHOOK_TOKEN']:
            update_payment_status.delay(request.data)
        else:
            capture_message(f'UNAUTHORIZED REQUEST | META: {request.META} | DATA: {request.data}')
        return Response({}, status.HTTP_200_OK)
