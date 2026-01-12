# Copyright (c) 2024 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2024 Alberto Gacías <alberto@migasfree.org>
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

from functools import wraps

from ..utils import hash_args


def unique_task(app):
    def decorator_task(callback):
        """
        Decorator to ensure only one instance of the task is running at once.
        """

        @wraps(callback)
        def wrapper(celery_task, *args, **kwargs):
            active_queues = app.control.inspect().active()
            if active_queues:
                for queue in active_queues:
                    for running_task in active_queues[queue]:
                        if celery_task.name == running_task['name'] and celery_task.request.id != running_task['id']:
                            # Serialize arguments and kwargs to create a unique identifier for the task
                            task_signature = hash_args(args, kwargs)
                            run_signature = hash_args(running_task['args'], running_task['kwargs'])
                            if task_signature == run_signature:
                                try:
                                    task_instance = celery_task.AsyncResult(celery_task.request.id)
                                    task_instance.revoke(terminate=True)
                                except Exception as e:
                                    return f'Error cancelling task "{callback.__name__}()": {e}'

            return callback(*args, **kwargs)

        return wrapper

    return decorator_task
