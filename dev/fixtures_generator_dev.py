import itertools
import uuid
from datetime import datetime, timedelta, timezone

from django.contrib.auth import get_user_model

from categories.models import Category
from customers.models import Customer
from orders.models import Order, Charge
from talents.models import Talent


User = get_user_model()

User.objects.all().delete()
Category.objects.all().delete()


# STAFF
superuser1 = User(
    username='superuser1@viggio.com.br',
    email='superuser1@viggio.com.br',
    first_name='Super',
    last_name='User',
    is_active=True,
    is_staff=True,
    is_superuser=True,
)
superuser2 = User(
    username='superuser2@viggio.com.br',
    email='superuser2@viggio.com.br',
    first_name='Super',
    last_name='User',
    is_active=True,
    is_staff=True,
    is_superuser=True,
)
superuser3 = User(
    username='superuser3@viggio.com.br',
    email='superuser3@viggio.com.br',
    first_name='Super',
    last_name='User',
    is_active=True,
    is_staff=True,
    is_superuser=True,
)
staff = User(
    username='staff@viggio.com.br',
    email='staff@viggio.com.br',
    first_name='Nome',
    last_name='Sobrenome',
    is_active=True,
    is_staff=True,
    is_superuser=False,
)
# TALENT
talents = [
    User(
        username=f'talento{number}@viggio.com.br',
        email=f'talento{number}@viggio.com.br',
        first_name=f'NomeT{number}',
        last_name=f'SobrenomeT{number}',
        is_active=True,
        is_staff=False,
        is_superuser=False,
    )
    for number in range(25)
]
# CUSTOMER
customers = [
    User(
        username=f'customer{number}@viggio.com.br',
        email=f'customer{number}@viggio.com.br',
        first_name=f'NomeC{number}',
        last_name=f'SobrenomeC{number}',
        is_active=True,
        is_staff=False,
        is_superuser=False,
    )
    for number in range(25)
]
users = [superuser1, superuser2, superuser3, staff] + talents + customers
User.objects.bulk_create(users)
users = User.objects.all()
for user in users:
    user.set_password('123')
    user.save()

users = User.objects.filter(email__startswith='talent') | User.objects.filter(is_staff=True)
descriptions = (
    'Você tá realmente obcecado pelos seus sonhos? Busque o next level. O segredo do sucesso é começar antes de estar pronto.',
    'Viva em busca da masterização e do profissionalismo, every f*ing day. Felicidade é a nova produtividade. O segredo do sucesso é começar antes de estar pronto.',
    'Busque o next level. Não adianta ter conhecimento se você não tem action. Se você não vê a oportunidade, ela passa.',
    'Encare problemas como oportunidades. O inconformismo é o combustível da alta performance. Desafie-se. Transforme o seu lifestyle.',
    'É você quem decide se o seu dia vai ser incrível ou não.  Não adianta ter conhecimento se você não tem action. Genialidade é fruto de muito hardwork. A vida acontece de você e não pra você.',
    'O segredo do sucesso é começar antes de estar pronto. Encare problemas como oportunidades. Busque o next level. O segredo do sucesso é começar antes de estar pronto.',
)
descriptions_cycle = itertools.cycle(descriptions)
talents = (
    Talent(
        user=user,
        phone_number=987654321,
        area_code=11,
        main_social_media='Instagram',
        social_media_username='socialusername',
        number_of_followers='29875134',
        price=150,
        description=next(descriptions_cycle),
        available=True,
    )
    for user in users
)
Talent.objects.bulk_create(talents)

talents = Talent.objects.all()

customers = (
    Customer(
        user=talent.user,
        avatar=None,
        phone_number=987654321,
        area_code=12,
        mailing_list=False,
    )
    for talent in talents
)
Customer.objects.bulk_create(customers)

users = User.objects.filter(email__startswith='customer')
customers = (
    Customer(
        user=user,
        avatar=None,
        phone_number=987654321,
        area_code=12,
        mailing_list=True,
    )
    for user in users
)
Customer.objects.bulk_create(customers)

talents = Talent.objects.all()
customers = Customer.objects.all().order_by('-id')[:5]
customers = list(customers) + [None] * 20
customers_cycle = itertools.cycle(customers)

emails = (f'customer{num}@not_authenticated.com' for num in range(51))
emails_cycle = itertools.cycle(emails)

is_for = ['someone_else'] * 15 + ['myself'] * 5
is_for_cycle = itertools.cycle(is_for)

orders = []
for talent in talents:
    for num in range(1, 26):
        orders.append(
            Order(
                hash_id=uuid.uuid4(),
                customer=next(customers_cycle),
                talent=talent,
                video_is_for=next(is_for_cycle),
                is_from='CustomerName',
                is_to='FriendName',
                instruction='Eiiitaaa Mainhaaa!! Esse Lorem ipsum é só na sacanageeem!! E que abundância meu irmão viuu!! Assim você vai matar o papai. Só digo uma coisa, Domingo ela não vai! Danadaa!! Vem minha odalisca, agora faz essa cobra coral subir!!!',
                email=next(emails_cycle),
                phone_number=987654321,
                area_code=12,
                is_public=True,
                expiration_datetime=datetime.now(timezone.utc).date() + timedelta(days=num),
            )
        )
orders = Order.objects.bulk_create(orders)

charges = []
for order in orders:
    charges.append(
        Charge(
            order=order,
            amount_paid='150.00',
            payment_date=datetime.now(timezone.utc),
            payment_method='credit_card',
            status='paid',
        )
    )
Charge.objects.bulk_create(charges)

CATEGORIES_DATA = (
    ('Youtubers', 'youtubers'),
    ('Influencers', 'influencers'),
    ('Atletas', 'athletes'),
    ('Músicos', 'musicians'),
    ('Caridade', 'charity'),
)

categories = (
    Category(name=category_data[0], slug=category_data[1])
    for category_data in CATEGORIES_DATA
)
categories = Category.objects.bulk_create(categories)

categories_to_cycle = (
    categories[:2],
    categories[:2],
    categories[2:],
    [categories[3]],
)
categories_cycle = itertools.cycle(categories_to_cycle)

for talent in Talent.objects.filter(user__email__startswith='talent').order_by('id'):
    talent.categories.set(next(categories_cycle))


# python manage.py dumpdata orders --indent 4 > orders/fixtures/orders_dev.json
# python manage.py dumpdata accounts --indent 4 > accounts/fixtures/accounts_dev.json
# python manage.py dumpdata customers --indent 4 > customers/fixtures/customer_dev.json
# python manage.py dumpdata talents --indent 4 > talents/fixtures/talent_dev.json
# python manage.py dumpdata categories --indent 4 > categories/fixtures/categories_dev.json
