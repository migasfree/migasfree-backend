# -*- coding: utf-8 -*-

# Copyright (c) 2015-2025 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2025 Alberto Gacías <alberto@migasfree.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os
import requests
import ssl
import urllib.request

from datetime import datetime, timedelta
from urllib.parse import urljoin
from celery import Celery, shared_task

from .models import Deployment, ScheduleDelay
from .decorators import unique_task
from ..utils import get_setting


CELERY_BROKER_URL = get_setting('CELERY_BROKER_URL')

app = Celery('migasfree', broker=CELERY_BROKER_URL, backend=CELERY_BROKER_URL, fixups=[])


@app.task(bind=True)
@unique_task(app)
def migrate_db():
    # Please, don't move this import from here
    from django.core.management import call_command

    call_command('migrate', interactive=False)


@shared_task
def update_deployment_start_date():
    """
    Daily task that updates the start date of deployments
    that have auto_restart=True and have completed deployment.
    """
    deployments = Deployment.objects.filter(auto_restart=True, schedule__isnull=False)

    for deployment in deployments:
        schedule_delays = ScheduleDelay.objects.filter(schedule=deployment.schedule)
        if schedule_delays.exists():
            last_delay = schedule_delays.order_by('delay').last()
            if last_delay:
                start_date = deployment.start_date
                last_delay_date = start_date + timedelta(days=last_delay.delay)
                last_duration_date = last_delay_date + timedelta(days=last_delay.duration)

                if datetime.today().date() >= last_duration_date:
                    new_start_date = last_duration_date + timedelta(days=1)
                    deployment.start_date = new_start_date
                    deployment.save()
                    print(f"Updated the start date of deployment {deployment.name} to {new_start_date}")  # DEBUG


@shared_task
def remove_orphan_files_from_external_deployments():
    deployments = Deployment.objects.filter(source=Deployment.SOURCE_EXTERNAL, frozen=False)
    for deploy in deployments:
        path = deploy.path()
        if not os.path.isdir(path):
            continue

        for root, _, files in os.walk(path):
            for _file in files:
                file_path = os.path.join(root, _file)
                relative_path = file_path.split(f'{deploy.slug}/', 1)[1]
                url = urljoin(f'{deploy.base_url}/', relative_path)

                try:
                    with urllib.request.urlopen(
                        urllib.request.Request(url, method='HEAD'),
                        context=ssl.SSLContext(ssl.PROTOCOL_SSLv23)
                    ) as response:
                        headers = response.getheaders()

                        if response.status == requests.codes.not_found:
                            print(f'File {file_path} not found at server. Removed. (No catch)')
                            os.remove(file_path)
                            continue

                        file_size = os.path.getsize(file_path)

                        content_length = None
                        for header in headers:
                            if header[0].lower() == 'content-length':
                                content_length = int(header[1])
                                break

                        if content_length is not None and file_size != content_length:
                            print(
                                f'File size {file_path} ({file_size}) does not match '
                                f'the size on the server ({content_length}). Removed.'
                            )
                            os.remove(file_path)

                except urllib.error.HTTPError as e:
                    print(f'HTTP error accessing {url}: {e.code} {e.reason}')
                    if e.code == requests.codes.not_found:
                        print(f'File {file_path} not found at server. Removed.')
                        os.remove(file_path)
                except ConnectionResetError as e:
                    print(f'Connection reset accessing {url}: {e}')
                except urllib.error.URLError as e:
                    if requests.codes.not_found in str(e.reason):
                        print(f'File {file_path} not found at server. Removed.')
                        os.remove(file_path)
                    else:
                        print(f'Error accessing {url}: {e}')
