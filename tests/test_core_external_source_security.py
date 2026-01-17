from django.core.exceptions import ValidationError
from django.test import TestCase

from migasfree.core.models import ExternalSource, Platform, Project


class TestExternalSourceSecurity(TestCase):
    def setUp(self):
        self.platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(
            name='Test Project', pms='apt', architecture='amd64', platform=self.platform
        )

    def test_unsafe_base_url_validation(self):
        source = ExternalSource(
            name='Unsafe Source',
            slug='unsafe-source',
            id=1,
            project=self.project,
            base_url='http://127.0.0.1/ubuntu',
            source='E',
        )

        with self.assertRaises(ValidationError) as cm:
            source.clean()

        self.assertIn('base_url', cm.exception.message_dict)

    def test_safe_base_url_validation(self):
        source = ExternalSource(
            name='Safe Source',
            slug='safe-source',
            id=2,
            project=self.project,
            base_url='http://archive.ubuntu.com/ubuntu',
            source='E',
        )

        try:
            source.clean()
        except ValidationError:
            self.fail('clean() raised ValidationError unexpectedly for valid URL!')
