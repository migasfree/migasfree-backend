# migasfree-backend

Systems Management System (backend). Provides a REST API.

## Run in development mode (example)

```bash
pip3 install -r requirements/development.txt

python3 manage.py runserver 0.0.0.0:2345 --settings=migasfree.settings.development

DJANGO_SETTINGS_MODULE='migasfree.settings.development' celery --app=migasfree.celery.app beat --loglevel=DEBUG

DJANGO_SETTINGS_MODULE='migasfree.settings.development' celery --app=migasfree.celery.app worker --without-gossip --concurrency=10 --queues=default,pms-apt,pms-dnf,pms-pacman,pms-wpt,pms-yum,pms-zypper --loglevel=DEBUG
```

## View API endpoints (in development mode)

```bash
python3 manage.py show_urls --settings=migasfree.settings.development
```

## Update redis syncs stats (example)

```bash
python3 manage.py refresh_redis_syncs --settings=migasfree.settings.development --since 2020 --until=2021
```

## Redis stats structure

```text
migasfree:watch:stats:years:YYYY
migasfree:watch:stats:<project_id>:years:YYYY
migasfree:stats:years:YYYY
migasfree:stats:<project_id>:years:YYYY

migasfree:watch:stats:months:YYYYMM
migasfree:watch:stats:<project_id>:months:YYYYMM
migasfree:stats:months:YYYYMM
migasfree:stats:<project_id>:months:YYYYMM

migasfree:watch:stats:days:YYYYMMDD
migasfree:watch:stats:<project_id>:days:YYYYMMDD
migasfree:stats:days:YYYYMMDD
migasfree:stats:<project_id>:days:YYYYMMDD

migasfree:watch:stats:hours:YYYYMMDDHH
migasfree:watch:stats:<project_id>:hours:YYYYMMDDHH
migasfree:stats:hours:YYYYMMDDHH
migasfree:stats:<project_id>:hours:YYYYMMDDHH
```

## Code coverage (in development mode)

```bash
python3 -m pytest --cov=migasfree
```
