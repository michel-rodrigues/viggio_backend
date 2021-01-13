from django.contrib import admin
from .models import ShoutoutVideo


class ShoutoutVideoAdmin(admin.ModelAdmin):

    search_fields = ['hash_id', 'order__hash_id', 'talent__user__email']


admin.site.register(ShoutoutVideo, ShoutoutVideoAdmin)
