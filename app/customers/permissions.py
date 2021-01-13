from rest_framework import permissions

from .models import Customer


class CustomerAccessPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return Customer.objects.filter(user=request.user).exists()
