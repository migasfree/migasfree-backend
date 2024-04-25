# -*- coding: utf-8 -*-

# Copyright (c) 2015-2024 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2024 Alberto Gacías <alberto@migasfree.org>
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

from celery import Celery, shared_task

from .decorators import unique_task
from ..utils import get_setting


CELERY_BROKER_URL = get_setting('CELERY_BROKER_URL')

app = Celery('migasfree', broker=CELERY_BROKER_URL, backend=CELERY_BROKER_URL, fixups=[])


@shared_task(queue='default', bind=True)
@unique_task(app)
def migrate_db():
    # Please, don't move this import from here
    from django.core.management import call_command

    call_command('migrate', interactive=False)
