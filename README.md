# migasfree-backend

Systems Management System (backend). Provides a REST API.

## Run in development mode (example)

`$ python3 manage.py runserver 0.0.0.0:2345 --settings=migasfree.settings.development`

`$ DJANGO_SETTINGS_MODULE='migasfree.settings.development' celery --app=migasfree.celery.app worker --without-gossip --concurrency=10 -Q default -B`

`$ DJANGO_SETTINGS_MODULE='migasfree.settings.development' celery --app=migasfree.celery.app worker --without-gossip --concurrency=10 -Q repository`

## Update redis stats (example)

`$ python3 manage.py refresh_redis_syncs --settings=migasfree.settings.development --since 2020 --until=2021`
