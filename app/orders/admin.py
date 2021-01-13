from django.contrib import admin
from shoutouts.models import ShoutoutVideo
from wirecard.models import WirecardTransactionData

from .models import (
    AgencyProfit,
    AgencyProfitPercentage,
    Charge,
    CustomTalentProfitPercentage,
    TalentProfit,
    DefaultTalentProfitPercentage,
    Order,
)


MAX_OBJECTS = 1


class DefaultTalentProfitPercentageAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        if self.model.objects.count() >= MAX_OBJECTS:
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


class ChargeInLine(admin.StackedInline):
    model = Charge


class ShoutoutVideoInLine(admin.StackedInline):
    model = ShoutoutVideo


class TalentProfitInLine(admin.StackedInline):
    model = TalentProfit


class WirecardTransactionDataInLine(admin.StackedInline):
    model = WirecardTransactionData


class OrderAdmin(admin.ModelAdmin):

    search_fields = ['hash_id']
    inlines = [
        ChargeInLine,
        ShoutoutVideoInLine,
        TalentProfitInLine,
        WirecardTransactionDataInLine,
    ]


class ChargeAdmin(admin.ModelAdmin):

    search_fields = ['order__hash_id']


class TalentProfitAdmin(admin.ModelAdmin):

    search_fields = ['order__hash_id', 'talent__user__email']


class AgencyProfitAdmin(admin.ModelAdmin):

    search_fields = ['order__hash_id', 'name']


admin.site.register(AgencyProfitPercentage)
admin.site.register(AgencyProfit, AgencyProfitAdmin)
admin.site.register(Charge, ChargeAdmin)
admin.site.register(CustomTalentProfitPercentage)
admin.site.register(TalentProfit, TalentProfitAdmin)
admin.site.register(DefaultTalentProfitPercentage, DefaultTalentProfitPercentageAdmin)
admin.site.register(Order, OrderAdmin)
