from django.contrib import admin
from .models import Agency, AgencyBankAccount, PresentationVideo, Talent, TalentBankAccount


class PresentationVideoInline(admin.StackedInline):
    model = PresentationVideo


class TalentBankAccountInLine(admin.StackedInline):
    model = TalentBankAccount


class TalentAdmin(admin.ModelAdmin):

    search_fields = ['user__email']
    inlines = [PresentationVideoInline, TalentBankAccountInLine]


class AgencyBankAccountInLine(admin.StackedInline):
    model = AgencyBankAccount


class AgencyAdmin(admin.ModelAdmin):

    search_fields = ['user__email']
    inlines = [AgencyBankAccountInLine]


admin.site.register(Agency, AgencyAdmin)
admin.site.register(Talent, TalentAdmin)
