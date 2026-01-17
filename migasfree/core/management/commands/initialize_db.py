# Copyright (c) 2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2026 Alberto Gacías <alberto@migasfree.org>
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

import logging

from django.core import management
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError

from migasfree.fixtures import create_initial_data

logger = logging.getLogger('migasfree')


class Command(BaseCommand):
    help = 'Initialize database with migrations and default data if empty'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force running migrations even if tables exist',
        )
        parser.add_argument(
            '--skip-fixtures',
            action='store_true',
            help='Skip loading initial fixtures',
        )

    def handle(self, *args, **options):
        try:
            tables = connection.introspection.table_names()

            if not tables:
                self.stdout.write('No tables found. Running initial migrations...')
                logger.info('Starting database initialization')

                management.call_command('migrate', 'auth', interactive=False, verbosity=options['verbosity'])

                management.call_command('migrate', interactive=False, verbosity=options['verbosity'])

                if not options['skip_fixtures']:
                    self.stdout.write('Loading initial fixtures...')
                    create_initial_data()

                logger.info('Database initialization completed successfully')
                self.stdout.write(self.style.SUCCESS('Database initialized successfully'))
            elif options['force']:
                self.stdout.write('Force flag set. Running migrations...')
                logger.info('Running forced migrations')

                management.call_command('migrate', interactive=False, verbosity=options['verbosity'])

                self.stdout.write(self.style.SUCCESS('Migrations applied successfully'))
            else:
                self.stdout.write(
                    self.style.WARNING('Database already contains tables. Use --force to run migrations anyway.')
                )

        except OperationalError as e:
            logger.error('Database error during initialization: %s', e)
            self.stdout.write(self.style.ERROR(f'Database error: {e}'))
            raise
