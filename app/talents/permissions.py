from rest_framework import permissions

from .models import Talent


class TalentAccessPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return Talent.objects.filter(user=request.user).exists()
