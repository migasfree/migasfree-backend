from django.urls import path

from .consumers import TunnelConsumer

ws_urlpatterns = [
    path('ws/tunnel/computers/<int:computer_id>/', TunnelConsumer.as_asgi()),
]
