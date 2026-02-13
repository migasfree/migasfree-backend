import uuid

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.app_catalog.models import Application, Category, PackagesByProject
from migasfree.client.models import Computer
from migasfree.core.models import Attribute, Platform, Project, Property, UserProfile


class TestApplicationsViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(name='Vitalinux', pms='apt', architecture='amd64', platform=self.platform)

        property_att = Property.objects.create(name='some_property', prefix='SOM')
        att1 = Attribute.objects.create(property_att=property_att, value='one')
        att2 = Attribute.objects.create(property_att=property_att, value='two')

        self.computer = Computer.objects.create(
            name='PCXXXXX',
            project=self.project,
            uuid=str(uuid.uuid4()),
        )
        self.computer.sync_attributes.set([att1.id, att2.id])

        self.category = Category.objects.create(name='cat1')
        self.category2 = Category.objects.create(name='cat2')

        self.application1 = Application.objects.create(
            name='App 1', description='Description 1', category=self.category
        )
        self.application1.available_for_attributes.set([self.computer.sync_attributes.first()])
        PackagesByProject.objects.create(
            application=self.application1, project=self.project, packages_to_install='pkg1'
        )

        self.application2 = Application.objects.create(
            name='App 2', description='Description 2', category=self.category2
        )
        self.application2.available_for_attributes.set([self.computer.sync_attributes.first()])
        PackagesByProject.objects.create(
            application=self.application2, project=self.project, packages_to_install='pkg2'
        )

        self.application3 = Application.objects.create(
            name='App 3', description='Description 3', category=self.category2, level='A'
        )
        self.application3.available_for_attributes.set([self.computer.sync_attributes.first()])
        PackagesByProject.objects.create(
            application=self.application3, project=self.project, packages_to_install='pkg3'
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


class TestApplicationIcon(APITestCase):
    def setUp(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.user = UserProfile.objects.create(
            username='test_icon', email='test_icon@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(name='Test Category Icon')

        self.SimpleUploadedFile = SimpleUploadedFile

    def test_upload_svg_icon(self):
        svg_content = b'<svg height="100" width="100"><circle cx="50" cy="50" r="40" stroke="black" stroke-width="3" fill="red" /></svg>'
        svg_file = self.SimpleUploadedFile('icon.svg', svg_content, content_type='image/svg+xml')

        data = {
            'name': 'SVG App',
            'category': self.category.pk,
            'icon': svg_file,
        }
        response = self.client.post(reverse('application-list'), data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Application.objects.get(name='SVG App').icon.name.endswith('.svg'))

    def test_upload_png_icon(self):
        png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        png_file = self.SimpleUploadedFile('icon.png', png_content, content_type='image/png')

        data = {
            'name': 'PNG App',
            'category': self.category.pk,
            'icon': png_file,
        }
        response = self.client.post(reverse('application-list'), data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Application.objects.get(name='PNG App').icon.name.endswith('.png'))

    def test_upload_invalid_file(self):
        txt_content = b'This is a text file.'
        txt_file = self.SimpleUploadedFile('icon.txt', txt_content, content_type='text/plain')

        data = {
            'name': 'Invalid App',
            'category': self.category.pk,
            'icon': txt_file,
        }
        response = self.client.post(reverse('application-list'), data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('icon', response.json())

    def test_upload_webp_icon(self):
        webp_content = b'RIFF\x14\x00\x00\x00WEBPVP8 \x08\x00\x00\x00\x00\x01\x00\x01\x00\x00'
        webp_file = self.SimpleUploadedFile('icon.webp', webp_content, content_type='image/webp')

        data = {
            'name': 'WebP App',
            'category': self.category.pk,
            'icon': webp_file,
        }
        response = self.client.post(reverse('application-list'), data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Application.objects.get(name='WebP App').icon.name.endswith('.webp'))

    def test_upload_ico_icon(self):
        ico_content = b'\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00\x08\x00h\x00\x00\x00\x16\x00\x00\x00'
        ico_file = self.SimpleUploadedFile('icon.ico', ico_content, content_type='image/x-icon')

        data = {
            'name': 'ICO App',
            'category': self.category.pk,
            'icon': ico_file,
        }
        response = self.client.post(reverse('application-list'), data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Application.objects.get(name='ICO App').icon.name.endswith('.ico'))
