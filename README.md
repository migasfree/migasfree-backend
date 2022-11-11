# migasfree-backend

Systems Management System (backend). Provides a REST API.

## Run in development mode (example)

`$ python3 manage.py runserver 0.0.0.0:2345 --settings=migasfree.settings.development`

`$ DJANGO_SETTINGS_MODULE='migasfree.settings.development' celery --app=migasfree.celery.app worker --without-gossip --concurrency=10 -Q default -B`

`$ DJANGO_SETTINGS_MODULE='migasfree.settings.development' celery --app=migasfree.celery.app worker --without-gossip --concurrency=10 -Q repository`

## Update redis syncs stats (example)

`$ python3 manage.py refresh_redis_syncs --settings=migasfree.settings.development --since 2020 --until=2021`

## Redis stats structure

`migasfree:watch:stats:years:YYYY`<br>
`migasfree:watch:stats:<project_id>:years:YYYY`<br>
`migasfree:stats:years:YYYY`<br>
`migasfree:stats:<project_id>:years:YYYY`

`migasfree:watch:stats:months:YYYYMM`<br>
`migasfree:watch:stats:<project_id>:months:YYYYMM`<br>
`migasfree:stats:months:YYYYMM`<br>
`migasfree:stats:<project_id>:months:YYYYMM`

`migasfree:watch:stats:days:YYYYMMDD`<br>
`migasfree:watch:stats:<project_id>:days:YYYYMMDD`<br>
`migasfree:stats:days:YYYYMMDD`<br>
`migasfree:stats:<project_id>:days:YYYYMMDD`

`migasfree:watch:stats:hours:YYYYMMDDHH`<br>
`migasfree:watch:stats:<project_id>:hours:YYYYMMDDHH`<br>
`migasfree:stats:hours:YYYYMMDDHH`<br>
`migasfree:stats:<project_id>:hours:YYYYMMDDHH`
