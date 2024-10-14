import os

from django.conf import settings
from django.test import TestCase

from migasfree.core.models import Project


class TestProjectModel(TestCase):
    def test_path(self):
        name = 'my_project'
        expected = os.path.join(settings.MIGASFREE_PUBLIC_DIR, name)
        result = Project.path(name)
        assert result == expected

    def test_repositories_path(self):
        name = 'my_project'
        expected = os.path.join(settings.MIGASFREE_PUBLIC_DIR, name, settings.MIGASFREE_REPOSITORY_TRAILING_PATH)
        result = Project.repositories_path(name)
        assert result == expected

    def test_stores_path(self):
        name = 'my_project'
        expected = os.path.join(settings.MIGASFREE_PUBLIC_DIR, name, settings.MIGASFREE_STORE_TRAILING_PATH)
        result = Project.stores_path(name)
        assert result == expected

    def test_path_empty_name(self):
        name = ''
        expected = os.path.join(settings.MIGASFREE_PUBLIC_DIR, '')
        result = Project.path(name)
        assert result == expected

    def test_repositories_path_empty_name(self):
        name = ''
        expected = os.path.join(settings.MIGASFREE_PUBLIC_DIR, '', settings.MIGASFREE_REPOSITORY_TRAILING_PATH)
        result = Project.repositories_path(name)
        assert result == expected

    def test_stores_path_empty_name(self):
        name = ''
        expected = os.path.join(settings.MIGASFREE_PUBLIC_DIR, '', settings.MIGASFREE_STORE_TRAILING_PATH)
        result = Project.stores_path(name)
        assert result == expected
