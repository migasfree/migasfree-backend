import os
import time

from django.conf import settings
from django.db import connection


def get_saturation_metrics():
    """
    Get server saturation metrics (DB latency and CPU load).
    Returns a dict with 'saturated', 'db_latency', and 'load_percentage'.
    """
    # 1. Check Postgres latency
    start_time = time.time()
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        cursor.fetchone()
    db_latency = time.time() - start_time

    # 2. Check Load Average
    cpu_count = os.cpu_count() or 1
    load_avg_1m, _, _ = os.getloadavg()
    load_percentage = (load_avg_1m / cpu_count) * 100

    saturated = (
        db_latency > settings.MIGASFREE_SYNC_MAX_DB_LATENCY or load_percentage > settings.MIGASFREE_SYNC_MAX_CORE_LOAD
    )

    return {
        'saturated': saturated,
        'db_latency': db_latency,
        'load_percentage': load_percentage,
    }


def is_server_saturated():
    """
    Check if the server is saturated based on DB latency and CPU load.
    Returns True if saturated, False otherwise.
    """
    return get_saturation_metrics()['saturated']
