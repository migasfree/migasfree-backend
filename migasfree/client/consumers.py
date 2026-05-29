import asyncio
import urllib.parse

import websockets
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.core.exceptions import PermissionDenied
from rest_framework.authtoken.models import Token

from migasfree.core.models.user_profile import UserProfile


@database_sync_to_async
def get_user_from_token(token_key):
    try:
        token = Token.objects.select_related('user').get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return None


@database_sync_to_async
def validate_user_scope(user, computer_id):
    try:
        profile = UserProfile.objects.get(id=user.id)
        profile.check_scope(computer_id)
        return True
    except (UserProfile.DoesNotExist, PermissionDenied):
        return False


class TunnelConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.computer_id = self.scope['url_route']['kwargs']['computer_id']

        # Parse query params
        query_string = self.scope.get('query_string', b'').decode('utf-8')
        query_params = urllib.parse.parse_qs(query_string)

        token_key = query_params.get('token', [None])[0]
        service = query_params.get('service', [None])[0]
        username = query_params.get('user', [None])[0]

        if not token_key or not service:
            await self.accept()
            await self.close(code=4000)
            return

        user = await get_user_from_token(token_key)
        if not user:
            await self.accept()
            await self.close(code=4003)
            return

        is_authorized = await validate_user_scope(user, self.computer_id)
        if not is_authorized:
            await self.accept()
            await self.close(code=4003)
            return

        # Build upstream URL
        manager_url = settings.MIGASFREE_MANAGER_URL
        ws_base = manager_url.replace('http://', 'ws://').replace('https://', 'wss://').rstrip('/')
        upstream_url = f'{ws_base}/manager/v1/private/tunnel/ws/agents/{self.computer_id}?service={service}'
        if username:
            upstream_url += f'&user={urllib.parse.quote(username)}'

        try:
            self.upstream = await websockets.connect(upstream_url)
        except Exception:
            await self.accept()
            await self.close(code=4004)
            return

        await self.accept()

        # Start forwarding loop from upstream to client
        self.upstream_task = asyncio.ensure_future(self.forward_upstream())

    async def disconnect(self, close_code):
        if hasattr(self, 'upstream_task'):
            self.upstream_task.cancel()
        if hasattr(self, 'upstream'):
            await self.upstream.close()

    async def receive(self, text_data=None, bytes_data=None):
        if hasattr(self, 'upstream'):
            if text_data is not None:
                await self.upstream.send(text_data)
            elif bytes_data is not None:
                await self.upstream.send(bytes_data)

    async def forward_upstream(self):
        try:
            async for message in self.upstream:
                if isinstance(message, bytes):
                    await self.send(bytes_data=message)
                else:
                    await self.send(text_data=message)
        except websockets.exceptions.ConnectionClosed:
            pass
        except asyncio.CancelledError:
            pass
        finally:
            await self.close()
