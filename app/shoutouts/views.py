from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ShoutoutVideo
from .serializers import ShoutoutSerializer


class ShoutoutDetailAPIView(APIView):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        shoutout_hash = kwargs['shoutout_hash']
        shoutout = get_object_or_404(ShoutoutVideo, hash_id=shoutout_hash)
        serialized = ShoutoutSerializer(shoutout)
        return Response(serialized.data, status.HTTP_200_OK)
