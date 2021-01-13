import uuid
from datetime import datetime
from django.contrib.auth import get_user_model
from django.db import models

from request_shoutout.domain.models import Charge as DomainCharge, Order as DomainOrder
from talents.models import Agency, Talent
from utils.base_models import BaseModel


User = get_user_model()


VIDEO_IS_FOR_CHOICES = (
    (DomainOrder.SOMEONE_ELSE, 'someone else'),
    (DomainOrder.MYSELF, 'myself'),
)


class Order(BaseModel):
    hash_id = models.UUIDField(unique=True, default=uuid.uuid4)
    talent = models.ForeignKey(Talent, on_delete=models.CASCADE)
    video_is_for = models.CharField(max_length=100, choices=VIDEO_IS_FOR_CHOICES)
    is_from = models.CharField(max_length=80, blank=True)
    is_to = models.CharField(max_length=80)
    instruction = models.TextField(blank=True)
    email = models.EmailField()
    expiration_datetime = models.DateTimeField()
    is_public = models.BooleanField()

    def __str__(self):
        return f'customer: {self.email} - talent: {self.talent}'

    @classmethod
    def persist(cls, domain_order):
        order, created = cls.objects.update_or_create(
            id=domain_order.id,
            defaults={
                'hash_id': domain_order.hash_id,
                'talent_id': domain_order.talent_id,
                'video_is_for': domain_order.video_is_for,
                'is_from': domain_order.is_from or '',
                'is_to': domain_order.is_to,
                'instruction': domain_order.instruction,
                'email': domain_order.email,
                'expiration_datetime': domain_order.expiration_datetime,
                'is_public': domain_order.is_public,
            },
        )
        domain_order.id = order.id
        domain_order.created_at = order.created_at
        return domain_order


STATUS_CHOICES = (
    (DomainCharge.NOT_PROCESSED, 'not processed'),
    (DomainCharge.PROCESSING, 'processing'),
    (DomainCharge.PRE_AUTHORIZED, 'pre-authorized'),
    (DomainCharge.PAID, 'paid'),
    (DomainCharge.FAILED, 'failed'),
    (DomainCharge.CANCELLED, 'cancelled'),
)


class Charge(BaseModel):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='charge')
    amount_paid = models.DecimalField(max_digits=7, decimal_places=2)
    payment_date = models.DateTimeField()
    payment_method = models.CharField(max_length=50)
    status = models.CharField(max_length=100, choices=STATUS_CHOICES)

    def __str__(self):
        return f'customer: {self.order.email} - amount: {self.amount_paid} - {self.status}'

    @classmethod
    def persist(cls, domain_charge):
        charge, created = cls.objects.update_or_create(
            order_id=domain_charge.order_id,
            defaults={
                'amount_paid': domain_charge.amount_paid,
                'payment_date': domain_charge.payment_date,
                'payment_method': domain_charge.payment_method,
                'status': domain_charge.status,
            }
        )
        domain_charge.id = charge.id
        return domain_charge


class CreditCard(BaseModel):
    charge = models.OneToOneField(
        Charge,
        on_delete=models.CASCADE,
        related_name='funding_instrument',
    )
    fullname = models.CharField(max_length=100)
    birthdate = models.DateField()
    tax_document = models.CharField(max_length=11)  # CPF
    phone_number = models.CharField(max_length=9)
    area_code = models.CharField(max_length=2)
    credit_card_hash = models.CharField(max_length=550)

    @classmethod
    def persist(cls, domain_credit_card):
        credit_card, created = cls.objects.update_or_create(
            charge_id=domain_credit_card.charge_id,
            defaults={
                'fullname': domain_credit_card.fullname,
                'birthdate': datetime.strptime(domain_credit_card.birthdate, '%d/%m/%Y').date(),
                'tax_document': domain_credit_card.tax_document,
                'phone_number': domain_credit_card.phone_number,
                'area_code': domain_credit_card.area_code,
                'credit_card_hash': domain_credit_card.credit_card_hash,
            }
        )


class Buyer(BaseModel):
    charge = models.OneToOneField(Charge, on_delete=models.CASCADE, related_name='buyer')
    fullname = models.CharField(max_length=100)
    birthdate = models.DateField()
    tax_document = models.CharField(max_length=11)  # CPF
    phone_number = models.CharField(max_length=9)
    area_code = models.CharField(max_length=2)

    @classmethod
    def persist(cls, domain_buyer):
        credit_card, created = cls.objects.update_or_create(
            charge_id=domain_buyer.charge_id,
            defaults={
                'fullname': domain_buyer.fullname,
                'birthdate': datetime.strptime(domain_buyer.birthdate, '%d/%m/%Y').date(),
                'tax_document': domain_buyer.tax_document,
                'phone_number': domain_buyer.phone_number,
                'area_code': domain_buyer.area_code,
            }
        )


class CustomTalentProfitPercentage(BaseModel):
    talent = models.OneToOneField(Talent, on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=3, decimal_places=2)

    def __str__(self):
        return f'{self.talent} - margem: {self.value * 100}%'


class DefaultTalentProfitPercentage(BaseModel):
    value = models.DecimalField(max_digits=3, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.pk and self.__class__.objects.count():
            raise Exception('Duplicar a porcentagem da margem padrão dos talentos NÃO PODE')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Margem padrão dos talentos: {self.value * 100}%'


class TalentProfit(BaseModel):
    talent = models.ForeignKey(Talent, on_delete=models.CASCADE, related_name='profits')
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='talent_profit')
    shoutout_price = models.DecimalField(max_digits=7, decimal_places=2)
    profit_percentage = models.DecimalField(max_digits=3, decimal_places=2)
    profit = models.DecimalField(max_digits=7, decimal_places=2)
    paid = models.BooleanField()

    def __str__(self):
        return f'{self.talent} - profit: {self.profit} - paid: {self.paid}'

    @classmethod
    def persist(cls, domain_talent_profit):
        cls.objects.create(
            talent_id=domain_talent_profit.talent_id,
            order_id=domain_talent_profit.order_id,
            shoutout_price=domain_talent_profit.shoutout_price,
            profit_percentage=domain_talent_profit.profit_percentage,
            profit=domain_talent_profit.profit,
            paid=domain_talent_profit.paid,
        )


class AgencyProfitPercentage(BaseModel):
    agency = models.OneToOneField(Agency, on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=3, decimal_places=2)

    def __str__(self):
        return f'{self.agency} - margem: {self.value * 100}%'


class AgencyProfit(BaseModel):
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name='profits')
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='agency_profit')
    shoutout_price = models.DecimalField(max_digits=7, decimal_places=2)
    profit_percentage = models.DecimalField(max_digits=3, decimal_places=2)
    profit = models.DecimalField(max_digits=7, decimal_places=2)
    paid = models.BooleanField()

    def __str__(self):
        return f'{self.agency} - profit: {self.profit} - paid: {self.paid}'

    @classmethod
    def persist(cls, domain_agency_profit):
        cls.objects.create(
            agency_id=domain_agency_profit.agency_id,
            order_id=domain_agency_profit.order_id,
            shoutout_price=domain_agency_profit.shoutout_price,
            profit_percentage=domain_agency_profit.profit_percentage,
            profit=domain_agency_profit.profit,
            paid=domain_agency_profit.paid,
        )
