#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $DATABASE_HOST $DATABASE_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# python manage.py flush --no-input
python manage.py migrate
# python manage.py loaddata accounts_dev.json
# python manage.py loaddata categories_dev.json
# python manage.py loaddata talent_dev.json
# python manage.py loaddata customer_dev.json
# python manage.py loaddata orders_dev.json
python manage.py collectstatic --no-input --clear
supervisord -c supervisord.conf
python manage.py runserver 0.0.0.0:8000 --settings=project_configuration.settings.development

exec "$@"
