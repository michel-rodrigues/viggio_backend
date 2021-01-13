import io
from datetime import date

from django.core.files.storage import default_storage
from django.core.management import BaseCommand
from django.db import transaction

from orders.models import TalentProfit
from talents.management.services.payment import (
    get_talents_to_be_paid_in_the_month,
    talent_payment_csv_columns_mapper,
    TALENT_PAYMENT_CSV_HEADER,
    TALENT_PAYMENT_CSV_PATH_TEMPLATE,
)
from talents.models import TalentProfitsPaymentLog
from utils.csv_reader import CSVReader


class Command(BaseCommand):
    """Read a CSV in the storage or a provided local CSV path
    to update TalentProfits status on the reference's month.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            type=str,
            help=''
        )
        parser.add_argument(
            '--month',
            type=int,
            help=''
        )
        parser.add_argument(
            '--year',
            type=int,
            help=''
        )

    def _is_valid(self, data, talent):
        return all((
            data['paid'],
            data['total_paid'] == talent.total_to_pay,
            data['num_profits'] == talent.num_profits,
        ))

    def _process_csv(self, csv_file, month, year):
        talents = get_talents_to_be_paid_in_the_month(month, year)
        talents_map = {
            talent.user.email: talent
            for talent in talents
        }
        csv_reader = CSVReader(
            file_object=csv_file,
            header=TALENT_PAYMENT_CSV_HEADER,
            columns_mapper=talent_payment_csv_columns_mapper,
            delimiter=','
        )
        for data in csv_reader.get_data():
            talent = talents_map.get(data['talent_email'])
            if not talent:
                message = f'There are no talent_profits for {data["talent_email"]}\n'
                self.stdout.write(self.style.WARNING(message))
                continue
            if not self._is_valid(data, talent):
                # csv paid field has to be True and the rest of the values has to be equal
                message = (
                    f'There add_argument an issue with {data["talent_email"]}\n'
                    '-------------- CSV | DATABASE\n'
                    f'paid --------- {data["paid"]} |\n'
                    f'total_paid --- {data["total_paid"]} | {talent.total_to_pay}\n'
                    f'num_profits ---- {data["num_profits"]} | {talent.num_profits}\n'
                )
                self.stdout.write(self.style.WARNING(message))
                continue
            talent_profits = TalentProfit.objects.filter(
                talent_id=talent.id,
                paid=False,
                created_at__date__month=month,
                created_at__date__year=year,
            )
            if not talent_profits.count() == data['num_profits']:
                message = (
                    "Number of TalentProfits from CSV and DB doesn't match\n"
                    f'CSV: data["num_profits"] | DB: talent_profits.count()'
                    f'Talent: {talent}'
                )
                self.stdout.write(self.style.WARNING(message))
                continue
            talent_profits_ids = list(talent_profits.values_list('id', flat=True))
            with transaction.atomic():
                talent_profits.update(paid=True)
                TalentProfitsPaymentLog.objects.create(
                    talent_id=talent.id,
                    num_viggios=data['num_profits'],
                    amount_paid=data['total_paid'],
                    reference_month=date(year, month, 1),
                    paid_profits_ids_array=talent_profits_ids,
                )
            self.stdout.write(f'{talent} processed...')

    def _decode_from_bytes(self, csv_file):
        stream_text = io.StringIO()
        for row in csv_file:
            if isinstance(row, bytes):
                row = row.decode('utf-8')
            stream_text.write(row)
        return stream_text

    def _get_csv_from_storage(self, csv_storage_path):
        with default_storage.open(csv_storage_path, 'r') as csv_file:
            return self._decode_from_bytes(csv_file)

    def handle(self, *args, **options):
        month = options['month']
        year = options['year']
        csv_path = options['csv']
        if csv_path:
            with open(csv_path, 'r') as csv_file:
                self._process_csv(csv_file, month, year)
        else:
            csv_storage_path = TALENT_PAYMENT_CSV_PATH_TEMPLATE.format(month=month, year=year)
            if default_storage.exists(csv_storage_path):
                stream_text = self._get_csv_from_storage(csv_storage_path)
                self._process_csv(stream_text, month, year)
            else:
                message = 'There are no CSV on the storage or the provided CSV path is not valid.'
                self.stdout.write(self.style.ERROR(message))
        self.stdout.write(self.style.SUCCESS('Process finished'))
