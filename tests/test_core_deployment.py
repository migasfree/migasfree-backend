import pytest

from django.utils import timezone
from datetime import timedelta, datetime

from migasfree.core.models import (
    Project, Platform, Deployment,
    Schedule, ScheduleDelay,
)
from migasfree.utils import time_horizon


@pytest.fixture
def now():
    return timezone.now()


@pytest.fixture
def platform():
    return Platform.objects.create(name='Linux')


@pytest.fixture
def project(platform):
    return Project.objects.create(
        name='Vitalinux', platform=platform,
        pms='apt', architecture='amd64'
    )


@pytest.fixture
def schedule():
    return Schedule.objects.create(name='Standard')


@pytest.fixture
def deployment(project, schedule):
    return Deployment.objects.create(
        start_date=datetime.now(), project=project, schedule=schedule
    )


@pytest.fixture
def schedule_delays(deployment):
    ScheduleDelay.objects.create(schedule_id=deployment.schedule_id, delay=1, duration=2)
    ScheduleDelay.objects.create(schedule_id=deployment.schedule_id, delay=2, duration=3)

    return ScheduleDelay.objects.filter(schedule_id=deployment.schedule_id)


def test_get_percent_less_100_days(now):
    begin_date = now.date() - timedelta(days=5)
    end_date = now.date() + timedelta(days=5)

    assert Deployment.get_percent(begin_date, end_date) == 50


def test_get_percent_100(now):
    begin_date = now.date() - timedelta(days=1)
    end_date = now.date()

    assert Deployment.get_percent(begin_date, end_date) == 100


def test_get_percent_0(now):
    begin_date = now.date()
    end_date = now.date()

    assert Deployment.get_percent(begin_date, end_date) == 100


def test_get_percent_delayed(now):
    begin_date = now.date() - timedelta(days=10)
    end_date = now.date() - timedelta(days=5)

    assert Deployment.get_percent(begin_date, end_date) == 100


def test_get_percent_validate_return_value(now):
    begin_date = now.date()
    end_date = now.date()

    assert isinstance(Deployment.get_percent(begin_date, end_date), int)


@pytest.mark.django_db
def test_schedule_timeline_without_delays(deployment):
    deployment.schedule = None

    assert deployment.schedule_timeline() is None


@pytest.mark.django_db
def test_schedule_timeline_with_delays(deployment, schedule_delays):
    result = deployment.schedule_timeline()
    first_delay = schedule_delays.order_by('delay').first()
    last_delay = schedule_delays.order_by('delay').reverse().first()

    assert result['begin_date'] == str(time_horizon(deployment.start_date, first_delay.delay))
    assert result['end_date'] == str(time_horizon(deployment.start_date, last_delay.delay + last_delay.duration))


@pytest.mark.django_db
def test_schedule_timeline_percent(deployment, schedule_delays):
    result = deployment.schedule_timeline()

    assert 'percent' in result
    assert result['percent'] == 0
