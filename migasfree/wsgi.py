"""
WSGI config for migasfree project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os
import psutil

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "migasfree.settings.production")
application = get_wsgi_application()

p = psutil.Process(os.getpid())
p.ionice(psutil.IOPRIO_CLASS_IDLE)
