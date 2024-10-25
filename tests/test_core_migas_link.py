from django.http import HttpRequest
from django.test import TestCase

from migasfree.client.models import Computer
from migasfree.core.models import (
    Platform, Project, UserProfile,
    Property, Attribute, AttributeSet, Domain,
)


class TestMigasLink(TestCase):

    def setUp(self):
        self.platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(
            name='Vitalinux', platform=self.platform, pms='apt', architecture='amd64'
        )

        self.property_att = Property.objects.create(prefix='CID', name='Computer ID', sort='basic')

        self.request = HttpRequest()
        self.request.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.request.method = 'POST'

    def test_get_relations_computer(self):
        computer = Computer.objects.create(
            project=self.project, name='Computer1', uuid='12345678-1234-1234-1234-123456789012'
        )
        relations = computer.get_relations(self.request)

        self.assertIsNotNone(relations)
        assert isinstance(relations, list)

    def test_get_relations_attribute(self):
        attribute = Attribute.objects.create(property_att=self.property_att, value='1')
        relations = attribute.get_relations(self.request)

        self.assertIsNotNone(relations)
        assert isinstance(relations, list)

    def test_get_relations_attributeset(self):
        Property.objects.create(
            prefix='SET',
            name='Attribute Set',
            enabled=True,
            kind='N',
            sort='basic',
            language=1,
            code="print 'All Systems'"
        )
        attribute_set = AttributeSet.objects.create(name='Test Set')
        relations = attribute_set.get_relations(self.request)

        self.assertIsNotNone(relations)
        assert isinstance(relations, list)

    def test_get_relations_domain(self):
        domain = Domain.objects.create(name='Test Domain')
        relations = domain.get_relations(self.request)

        self.assertIsNotNone(relations)
        assert isinstance(relations, list)

    def test_badge_computer(self):
        computer = Computer.objects.create(
            project=self.project, name='Computer1', uuid='12345678-1234-1234-1234-123456789012'
        )
        badge = computer.badge()

        self.assertIsNotNone(badge)
        assert isinstance(badge, dict)
        assert 'status' in badge
        assert 'summary' in badge

    def test_badge_attribute(self):
        attribute = Attribute.objects.create(property_att=self.property_att, value='1')
        badge = attribute.badge()

        self.assertIsNotNone(badge)
        assert isinstance(badge, dict)
        assert 'pk' in badge
        assert 'text' in badge

    def test_badge_domain(self):
        domain = Domain.objects.create(name='Test Domain')
        badge = domain.badge()

        self.assertIsNotNone(badge)
        assert isinstance(badge, dict)
        assert 'status' in badge
        assert 'summary' in badge
