import os

from django.contrib.auth import get_user_model
from django.contrib.postgres import fields
from django.db import models
from django.utils.text import slugify

from categories.models import Category
from utils.base_models import BaseModel

User = get_user_model()


class Agency(BaseModel):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class AgencyBankAccount(BaseModel):
    agency = models.OneToOneField(Agency, on_delete=models.CASCADE, related_name='bank_account')
    fullname = models.CharField(max_length=100)
    tax_document = models.CharField(max_length=14)  # CPF ou CNPJ
    bank = models.CharField(max_length=80)  # Nome do banco
    bank_transit_number = models.CharField(max_length=10)  # Número do banco
    bank_branch_number = models.CharField(max_length=10)  # Número da agência
    account_number = models.CharField(max_length=10)  # Número da conta corrente
    account_control_digit = models.CharField(max_length=10, blank=True)  # Dígito da CC

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['account_number', 'bank_transit_number'],
                name='unique_agency_bank_account',
            )
        ]

    def __str__(self):
        return self.agency


class AgencyProfitsPaymentLog(BaseModel):
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE)
    num_viggios = models.PositiveSmallIntegerField()
    amount_paid = models.DecimalField(max_digits=7, decimal_places=2)
    reference_month = models.DateField()
    paid_profits_ids_array = fields.ArrayField(models.IntegerField())


class Talent(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # form de solicitação de perfil de talento
    phone_number = models.CharField(max_length=9)
    area_code = models.CharField(max_length=2)
    main_social_media = models.CharField(max_length=100)
    social_media_username = models.CharField(max_length=80)
    number_of_followers = models.PositiveIntegerField()
    # -- fim --
    # dados preenchidos depois que o talento é aceito
    price = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    description = models.TextField(blank=True)
    available = models.BooleanField(default=False)
    categories = models.ManyToManyField(
        Category,
        related_name='talents',
        related_query_name='talent',
    )
    agency = models.ForeignKey(
        Agency,
        on_delete=models.CASCADE,
        related_name='talents',
        blank=True,
        null=True,
    )
    # -- fim --

    def __str__(self):
        return self.user.email

    @property
    def profile_url(self):
        f'{os.environ["SITE_URL"]}perfil/{self.id}/'


def upload_location(instance, filename):
    extension = filename.split('.')[-1]
    name = slugify(''.join((filename.split('.')[:-1])))
    return f'presentation-video/talent-{instance.talent_id}/{name}.{extension}'


class PresentationVideo(BaseModel):
    talent = models.OneToOneField(
        Talent,
        on_delete=models.CASCADE,
        related_name='presentation_video',
    )
    file = models.FileField(upload_to=upload_location, max_length=140)

    def __str__(self):
        return f'ID:{self.id} - {self.talent}'


class TalentBankAccount(BaseModel):
    talent = models.OneToOneField(Talent, on_delete=models.CASCADE, related_name='bank_account')
    fullname = models.CharField(max_length=100)
    tax_document = models.CharField(max_length=14)  # CPF
    bank = models.CharField(max_length=80)  # Nome do banco
    bank_transit_number = models.CharField(max_length=10)  # Número do banco
    bank_branch_number = models.CharField(max_length=10)  # Número da agência
    account_number = models.CharField(max_length=10)  # Número da conta corrente
    account_control_digit = models.CharField(max_length=10, blank=True)  # Dígito da CC

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['account_number', 'bank_transit_number'],
                name='unique_talent_bank_account',
            )
        ]

    def __str__(self):
        return self.talent


class TalentProfitsPaymentLog(BaseModel):
    talent = models.ForeignKey(Talent, on_delete=models.CASCADE)
    num_viggios = models.PositiveSmallIntegerField()
    amount_paid = models.DecimalField(max_digits=7, decimal_places=2)
    reference_month = models.DateField()
    paid_profits_ids_array = fields.ArrayField(models.IntegerField())
