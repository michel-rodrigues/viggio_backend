import itertools
import random

from django.contrib.auth import get_user_model

from categories.models import Category
from customers.models import Customer
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

# TALENT
talents = [
    User(
        username='vsoares.bruno@gmail.com',
        email='vsoares.bruno@gmail.com',
        first_name='Charlie',
        last_name='Sheen',
        is_active=True,
        is_staff=False,
        is_superuser=False,
    ),
    User(
        username='lauraloyo.vqv@gmail.com',
        email='lauraloyo.vqv@gmail.com',
        first_name='Jeniffer',
        last_name='Morrison',
        is_active=True,
        is_staff=False,
        is_superuser=False,
    ),
    User(
        username='kathy@atriz.com',
        email='kathy@atriz.com',
        first_name='Kathy',
        last_name='Najimy',
        is_active=True,
        is_staff=False,
        is_superuser=False,
    ),
    User(
        username='michel.rodrigues86@yahoo.com.br',
        email='michel.rodrigues86@yahoo.com.br',
        first_name='Chuck',
        last_name='Liddell',
        is_active=True,
        is_staff=False,
        is_superuser=False,
    ),
    User(
        username='amy@atriz.com',
        email='amy@atriz.com',
        first_name='Amy',
        last_name='Hill',
        is_active=True,
        is_staff=False,
        is_superuser=False,
    ),
    User(
        username='jason@ator.com',
        email='jason@ator.com',
        first_name='Jason',
        last_name='David Frank',
        is_active=True,
        is_staff=False,
        is_superuser=False,
    ),
]
users = [superuser1, superuser2, superuser3] + talents
User.objects.bulk_create(users)

users = User.objects.all()
for user in users:
    user.set_password('123@mudar')
    user.save()


users = User.objects.all().exclude(email__endswith='viggio.com.br')

descriptions = (
    'Bacon ipsum dolor amet porchetta brisket andouille, frankfurter pastrami corned beef drumstick tri-tip. Kevin boudin kielbasa bresaola andouille biltong, sausage spare ribs shank.',
    'Burgdoggen pastrami sausage leberkas, shankle turducken ham kevin rump tongue tenderloin strip steak.',
    'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation.',
    'Ullamcorper dignissim cras tincidunt lobortis. Magna fermentum iaculis eu non diam phasellus vestibulum. Platea dictumst quisque sagittis purus sit amet volutpat.',
    'Lectus vestibulum mattis ullamcorper velit sed ullamcorper morbi. Tellus rutrum tellus pellentesque eu tincidunt tortor aliquam.Neque vitae tempus quam pellentesque nec nam aliquam.',
    'Pharetra sit amet aliquam id. Enim ut tellus elementum sagittis vitae et leo. Posuere sollicitudin aliquam ultrices sagittis orci. Amet risus nullam eget felis.',
)
descriptions_cycle = itertools.cycle(descriptions)
talents = (
    Talent(
        user=user,
        phone_number='987654321',
        area_code='11',
        main_social_media='Instagram',
        social_media_username='socialusername',
        number_of_followers='29875134',
        price=random.randint(20, 50),
        description=next(descriptions_cycle),
        available=True,
    )
    for user in users
)
Talent.objects.bulk_create(talents)

users = User.objects.all()

customers = (
    Customer(
        user=user,
        avatar=None,
        phone_number='987654321',
        area_code='12',
        mailing_list=False,
    )
    for user in users
)
Customer.objects.bulk_create(customers)

CATEGORIES_DATA = (
    ('Youtubers', 'youtubers'),
    ('Influencers', 'influencers'),
    ('Atores', 'actors'),
    ('Comediantes', 'comedians'),
    ('Dubladores', 'voice_actors'),
    ('Atletas', 'athletes'),
    ('Músicos', 'musicians'),
    ('Apresentadores', 'presenters'),
    ('Políticos', 'politicians'),
    ('Pro Players', 'pro_players'),
    ('Caridade', 'charity'),
)

categories = (
    Category(name=category_data[0], slug=category_data[1])
    for category_data in CATEGORIES_DATA
)
categories = Category.objects.bulk_create(categories)

talent = Talent.objects.get(user__first_name='Charlie')
talent.categories.set((
    Category.objects.get(slug='actors'),
    Category.objects.get(slug='comedians')
))

talent = Talent.objects.get(user__first_name='Jeniffer')
talent.categories.set([Category.objects.get(slug='actors')])

talent = Talent.objects.get(user__first_name='Kathy')
talent.categories.set([Category.objects.get(slug='actors')])

talent = Talent.objects.get(user__first_name='Chuck')
talent.categories.set([Category.objects.get(slug='athletes')])

talent = Talent.objects.get(user__first_name='Amy')
talent.categories.set((
    Category.objects.get(slug='actors'),
    Category.objects.get(slug='voice_actors'),
))

talent = Talent.objects.get(user__first_name='Jason')
talent.categories.set((
    Category.objects.get(slug='actors'),
    Category.objects.get(slug='athletes'),
))

# python manage.py dumpdata accounts --indent 4 > accounts/fixtures/accounts_dev.json && python manage.py dumpdata customers --indent 4 > customers/fixtures/customer_dev.json && python manage.py dumpdata talents --indent 4 > talents/fixtures/talent_dev.json && python manage.py dumpdata categories --indent 4 > categories/fixtures/categories_dev.json

# python manage.py dumpdata accounts --indent 4 > accounts/fixtures/accounts_dev.json
# python manage.py dumpdata customers --indent 4 > customers/fixtures/customer_dev.json
# python manage.py dumpdata talents --indent 4 > talents/fixtures/talent_dev.json
# python manage.py dumpdata categories --indent 4 > categories/fixtures/categories_dev.json
