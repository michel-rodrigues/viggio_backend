from django.core.management import BaseCommand


from talents.management.services.payment import (
    get_talents_to_be_paid_in_the_month,
    write_talent_payment_csv,
)


class Command(BaseCommand):
    """Write in the storage a CSV file with data to pay our debts
    with Talents in reference's month.
    """

    def add_arguments(self, parser):
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

    def handle(self, *args, **options):
        month = options['month']
        year = options['year']
        talents_to_be_paid = get_talents_to_be_paid_in_the_month(month, year)
        write_talent_payment_csv(talents_to_be_paid, month, year)
        self.stdout.write(self.style.SUCCESS('CSV created.'))
