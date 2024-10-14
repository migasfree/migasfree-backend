import pytest
import uuid

from datetime import datetime
from django.test import TestCase
from django.utils.timezone import make_aware

from migasfree.client.models import Computer
from migasfree.core.models import Project, Platform


@pytest.mark.django_db
class TestComputerModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        platform = Platform.objects.create(name='Linux')
        cls.project = Project.objects.create(
            platform=platform, name='Vitalinux', pms='apt', architecture='amd64'
        )
        cls.project_other = Project.objects.create(
            platform=platform, name='Vitalinux EDU', pms='apt', architecture='amd64'
        )

    def test_stacked_by_month_empty(self):
        result = Computer.stacked_by_month(None, make_aware(datetime(2022, 1, 1)))

        assert result == []

    def test_stacked_by_month_no_filter(self):
        computer = Computer._base_manager.create(uuid=uuid.uuid4(), project=self.project)
        Computer.objects.filter(pk=computer.pk).update(created_at=make_aware(datetime(2022, 1, 15)))
        computer = Computer._base_manager.create(uuid=uuid.uuid4(), project=self.project)
        Computer.objects.filter(pk=computer.pk).update(created_at=make_aware(datetime(2022, 1, 20)))
        computer = Computer._base_manager.create(uuid=uuid.uuid4(), project=self.project_other)
        Computer.objects.filter(pk=computer.pk).update(created_at=make_aware(datetime(2022, 2, 10)))

        result = Computer.stacked_by_month(None, make_aware(datetime(2022, 1, 1)))
        assert result == [
            {'year': 2022, 'month': 1, 'project_id': 1, 'count': 2},
            {'year': 2022, 'month': 2, 'project_id': 2, 'count': 1}
        ]

    def test_stacked_by_month_filter(self):
        computer = Computer._base_manager.create(uuid=uuid.uuid4(), project=self.project)
        Computer.objects.filter(pk=computer.pk).update(created_at=make_aware(datetime(2022, 1, 15)))
        computer = Computer._base_manager.create(uuid=uuid.uuid4(), project=self.project)
        Computer.objects.filter(pk=computer.pk).update(created_at=make_aware(datetime(2022, 1, 20)))
        computer = Computer._base_manager.create(uuid=uuid.uuid4(), project=self.project_other)
        Computer.objects.filter(pk=computer.pk).update(created_at=make_aware(datetime(2022, 2, 10)))

        result = Computer.stacked_by_month(None, make_aware(datetime(2022, 1, 1)), 'project_id')
        assert result == [
            {'year': 2022, 'month': 1, 'project_id': 1, 'count': 2},
            {'year': 2022, 'month': 2, 'project_id': 2, 'count': 1}
        ]

    def test_stacked_by_month_order(self):
        computer = Computer._base_manager.create(uuid=uuid.uuid4(), project=self.project)
        Computer.objects.filter(pk=computer.pk).update(created_at=make_aware(datetime(2022, 1, 15)))
        computer = Computer._base_manager.create(uuid=uuid.uuid4(), project=self.project)
        Computer.objects.filter(pk=computer.pk).update(created_at=make_aware(datetime(2022, 1, 20)))
        computer = Computer._base_manager.create(uuid=uuid.uuid4(), project=self.project_other)
        Computer.objects.filter(pk=computer.pk).update(created_at=make_aware(datetime(2022, 2, 10)))

        result = Computer.stacked_by_month(None, make_aware(datetime(2022, 1, 1)))
        assert result == [
            {'year': 2022, 'month': 1, 'project_id': 1, 'count': 2},
            {'year': 2022, 'month': 2, 'project_id': 2, 'count': 1}
        ]

    def test_stacked_by_month_year(self):
        computer = Computer._base_manager.create(uuid=uuid.uuid4(), project=self.project)
        Computer.objects.filter(pk=computer.pk).update(created_at=make_aware(datetime(2022, 1, 15)))
        computer = Computer._base_manager.create(uuid=uuid.uuid4(), project=self.project)
        Computer.objects.filter(pk=computer.pk).update(created_at=make_aware(datetime(2023, 1, 20)))

        result = Computer.stacked_by_month(None, make_aware(datetime(2022, 1, 1)))
        assert result == [
            {'year': 2022, 'month': 1, 'project_id': 1, 'count': 1},
            {'year': 2023, 'month': 1, 'project_id': 1, 'count': 1}
        ]
