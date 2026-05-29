"""
ASGI config for migasfree project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'migasfree.settings.production')

# Initialize Django ASGI application first to load AppRegistry
django_asgi_app = get_asgi_application()

# Import routing only AFTER Django ASGI application is initialized
from channels.auth import AuthMiddlewareStack  # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402

from .client.routing import ws_urlpatterns as client_ws_urlpatterns  # noqa: E402
from .stats.routing import ws_urlpatterns as stats_ws_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        'http': django_asgi_app,
        'websocket': AuthMiddlewareStack(URLRouter(stats_ws_urlpatterns + client_ws_urlpatterns)),
    }
)
