from django.contrib import admin
from .models import WirecardTransactionData


class WirecardTransactionDataAdmin(admin.ModelAdmin):
    search_fields = ['order__hash_id']


admin.site.register(WirecardTransactionData, WirecardTransactionDataAdmin)
