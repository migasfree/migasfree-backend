from django.conf import settings
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from migasfree.client.saturation import is_server_saturated


class SynchronizationAvailabilityView(APIView):
    """
    Endpoint to check server saturation before syncing.

    If server is saturated (DB latency or CPU load), returns 503
    and queues the sync request.
    Otherwise returns 200.
    """

    def post(self, request, *args, **kwargs):
        """
        Handle the sync request.
        """
        if not is_server_saturated():
            return Response({'status': 'ok'}, status=status.HTTP_200_OK)

        # Server is saturated
        cid = request.data.get('cid')

        if cid:
            # Add to Redis List "migasfree_sync_queue"
            try:
                con = get_redis_connection('default')
                # Check if CID is already in queue to avoid duplicates?
                # LPOS is O(N), maybe ignore for now or use a Set too.
                # For simplicity, just RPUSH.
                con.rpush('migasfree_sync_queue', cid)
            except Exception:
                # If redis fails, what to do?
                # Maybe just return 503 without queueing or log error.
                pass

        retry_after = getattr(settings, 'MIGASFREE_SYNC_QUEUE_PROCESS_INTERVAL', 30) * 5
        return Response({'status': 'saturated', 'retry_after': retry_after}, status=status.HTTP_429_TOO_MANY_REQUESTS)
