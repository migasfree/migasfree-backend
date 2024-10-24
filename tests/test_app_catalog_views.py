import uuid

from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse

from migasfree.app_catalog.models import Application, Category, PackagesByProject
from migasfree.client.models import Computer
from migasfree.core.models import UserProfile, Platform, Project, Attribute, Property


class TestApplicationsViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(
            name='Vitalinux', pms='apt', architecture='amd64', platform=self.platform
        )

        property_att = Property.objects.create(name='some_property', prefix='SOM')
        att1 = Attribute.objects.create(property_att=property_att, value='one')
        att2 = Attribute.objects.create(property_att=property_att, value='two')

        self.computer = Computer.objects.create(
            name='PCXXXXX', project=self.project, uuid=str(uuid.uuid4()),
        )
        self.computer.sync_attributes.set([att1.id, att2.id])

        self.category = Category.objects.create(name='cat1')
        self.category2 = Category.objects.create(name='cat2')

        self.application1 = Application.objects.create(
            name='App 1', description='Description 1', category=self.category
        )
        self.application1.available_for_attributes.set([self.computer.sync_attributes.first()])
        PackagesByProject.objects.create(
            application=self.application1, project=self.project,
            packages_to_install='pkg1'
        )

        self.application2 = Application.objects.create(
            name='App 2', description='Description 2', category=self.category2
        )
        self.application2.available_for_attributes.set([self.computer.sync_attributes.first()])
        PackagesByProject.objects.create(
            application=self.application2, project=self.project,
            packages_to_install='pkg2'
        )

        self.application3 = Application.objects.create(
            name='App 3', description='Description 3', category=self.category2, level='A'
        )
        self.application3.available_for_attributes.set([self.computer.sync_attributes.first()])
        PackagesByProject.objects.create(
            application=self.application3, project=self.project,
            packages_to_install='pkg3'
        )

    def test_available_applications(self):
        url = reverse('application-available')
        response = self.client.get(url, {'cid': self.computer.pk})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_available_applications_with_category(self):
        url = reverse('application-available')
        response = self.client.get(url, {'cid': self.computer.pk, 'category': self.category.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_available_applications_with_level(self):
        url = reverse('application-available')
        response = self.client.get(url, {'cid': self.computer.pk, 'level': 'A'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_available_applications_with_query(self):
        url = reverse('application-available')
        response = self.client.get(url, {'cid': self.computer.pk, 'q': 'App'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
