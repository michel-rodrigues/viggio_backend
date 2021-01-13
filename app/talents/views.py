import os

from django.shortcuts import get_object_or_404
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    RetrieveUpdateAPIView,
)
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from post_office.mailgun import async_mailgun_carrier
from request_shoutout.domain.emails.templates import MailRequest
from request_shoutout.domain.emails.template_builders import enroll_talent_template_builder
from shoutouts.models import ShoutoutVideo
from .models import Talent
from .permissions import TalentAccessPermission
from .serializers import (
    EnrollSerializer,
    ShoutoutSerializer,
    TalentDetailSerializer,
    TalentInfoSerializer,
)


class EnrollAPIView(CreateAPIView):
    serializer_class = EnrollSerializer

    def post(self, request, *args, **kwargs):
        to_staff = MailRequest(
            to_email=os.environ['STAFF_EMAIL'].split(','),
            from_email=os.environ['CONTACT_EMAIL'],
            template=enroll_talent_template_builder(request.data),
        )
        async_mailgun_carrier(to_staff)
        return super().post(request, *args, **kwargs)


class RetrieveTalentAPIView(RetrieveAPIView):
    serializer_class = TalentDetailSerializer
    queryset = Talent.objects.all()

    def get_object(self):
        return get_object_or_404(Talent, id=self.kwargs['talent_id'])

    def retrieve(self, request, *args, **kwargs):
        talent = self.get_object()
        serializer = self.serializer_class(talent)
        return Response(serializer.data)


class TalentListAPIView(ListAPIView):
    serializer_class = TalentDetailSerializer
    queryset = Talent.objects.filter(available=True).order_by('?')


class RetrieveUpdateTalentAPIView(RetrieveUpdateAPIView):
    """Retorna ou atualiza informações confidenciais de um talento"""
    permission_classes = (IsAuthenticated, TalentAccessPermission)
    parser_class = (FileUploadParser,)
    serializer_class = TalentInfoSerializer
    queryset = Talent.objects.all()

    def get_object(self):
        return get_object_or_404(Talent, user_id=self.request.user.id)


class TalentShoutoutListAPIView(ListAPIView):
    serializer_class = ShoutoutSerializer

    def get_queryset(self):
        return ShoutoutVideo.objects.filter(
            talent_id=self.kwargs['talent_id'],
            order__is_public=True,
        )
