from decimal import Decimal

from django.db.models import Count, Sum
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from talents.models import Talent


TALENT_PAYMENT_CSV_HEADER = [
    'Email',
    'Nº de viggios',
    'Total',
    'Nome',
    'Conta Corrente',
    'Dígito',
    'Agência',
    'CPF/CNPJ',
    'Banco',
    'Pago?',
]

TALENT_PAYMENT_CSV_PATH_TEMPLATE = (
    'talents/payments/{year}/{month}/payment_control_{month}_{year}.csv'
)


def get_talents_to_be_paid_in_the_month(month, year):
    talents_to_be_paid_in_the_month = (
        Talent.objects
        .filter(
            profits__paid=False,
            profits__created_at__date__month=month,
            profits__created_at__date__year=year,
        )
        .prefetch_related('bank_account')
        .annotate(
            total_to_pay=Sum('profits__profit'),
            num_profits=Count('profits')
        )
    )
    return talents_to_be_paid_in_the_month


def write_talent_payment_csv(talents, month, year):
    content = ContentFile(b'')
    header = ','.join(TALENT_PAYMENT_CSV_HEADER)
    content.write(bytes(header, 'utf-8'))
    for talent in talents:
        row = (
            '\n'
            f'{talent},{talent.num_profits},{talent.total_to_pay},'
            f'{talent.bank_account.fullname},{talent.bank_account.account_number},'
            f'{talent.bank_account.account_control_digit},'
            f'{talent.bank_account.bank_branch_number},{talent.bank_account.tax_document},'
            f'{talent.bank_account.bank_transit_number} - {talent.bank_account.bank},'
        )
        content.write(bytes(row, 'utf-8'))
    path_to_save = TALENT_PAYMENT_CSV_PATH_TEMPLATE.format(month=month, year=year)
    default_storage.save(path_to_save, content)


def talent_payment_csv_columns_mapper(rows):
    return [
        {
            'talent_email': row['Email'],
            'num_profits': int(row['Nº de viggios']),
            'total_paid': Decimal(row['Total']),
            'paid': row['Pago?'] == 'sim',
        }
        for row in rows
    ]
