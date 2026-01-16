from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.core.models import Attribute, Domain, Property, Scope, UserProfile


class TestUserProfileViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='admin', email='admin@test.com', password='admin', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.test_user = UserProfile.objects.create(username='testuser', email='testuser@test.com', password='test')

    def test_list_users(self):
        response = self.client.get(reverse('userprofile-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)
        self.assertGreaterEqual(response.json()['count'], 2)

    def test_retrieve_user(self):
        response = self.client.get(reverse('userprofile-detail', kwargs={'pk': self.test_user.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['username'], self.test_user.username)

    def test_create_user(self):
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'password123',
        }
        response = self.client.post(reverse('userprofile-list'), data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['username'], data['username'])

    def test_update_user(self):
        data = {'first_name': 'John', 'last_name': 'Doe'}
        response = self.client.patch(reverse('userprofile-detail', kwargs={'pk': self.test_user.pk}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['first_name'], data['first_name'])

    def test_search_user(self):
        response = self.client.get(reverse('userprofile-list'), {'search': 'testuser'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.json()['count'], 1)

    def test_set_token(self):
        response = self.client.post(reverse('userprofile-set-token', kwargs={'pk': self.test_user.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('info', response.json())

    def test_change_password(self):
        data = {'password': 'newpassword123', 'password2': 'newpassword123'}
        response = self.client.put(reverse('userprofile-set-password', kwargs={'pk': self.test_user.pk}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestGroupViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='admin', email='admin@test.com', password='admin', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.group = Group.objects.create(name='Test Group')

    def test_list_groups(self):
        response = self.client.get(reverse('group-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)

    def test_retrieve_group(self):
        response = self.client.get(reverse('group-detail', kwargs={'pk': self.group.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], self.group.name)

    def test_create_group(self):
        data = {'name': 'New Group', 'permissions': []}
        response = self.client.post(reverse('group-list'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], data['name'])

    def test_update_group(self):
        data = {'name': 'Updated Group'}
        response = self.client.patch(reverse('group-detail', kwargs={'pk': self.group.pk}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], data['name'])

    def test_delete_group(self):
        group = Group.objects.create(name='ToDelete')
        response = self.client.delete(reverse('group-detail', kwargs={'pk': group.pk}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Group.objects.filter(pk=group.pk).exists())


class TestPermissionViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='admin', email='admin@test.com', password='admin', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

    def test_list_permissions(self):
        response = self.client.get(reverse('permission-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)
        # Permissions exist from Django's built-in models
        self.assertGreater(response.json()['count'], 0)


class TestDomainViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='admin', email='admin@test.com', password='admin', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.property_att = Property.objects.create(name='Test Property', prefix='TST')
        self.attribute = Attribute.objects.create(property_att=self.property_att, value='value1')

        self.domain = Domain.objects.create(name='Test Domain')
        self.domain.included_attributes.add(self.attribute)

    def test_list_domains(self):
        response = self.client.get(reverse('domain-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)
        self.assertGreaterEqual(response.json()['count'], 1)

    def test_retrieve_domain(self):
        response = self.client.get(reverse('domain-detail', kwargs={'pk': self.domain.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], self.domain.name)

    def test_create_domain(self):
        data = {
            'name': 'New Domain',
            'included_attributes': [self.attribute.pk],
            'excluded_attributes': [],
            'tags': [],
            'domain_admins': [self.user.pk],
        }
        response = self.client.post(reverse('domain-list'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Domain name is converted to uppercase slug
        self.assertEqual(response.json()['name'], 'NEW-DOMAIN')

    def test_update_domain(self):
        data = {'name': 'Updated Domain', 'domain_admins': [self.user.pk]}
        response = self.client.patch(reverse('domain-detail', kwargs={'pk': self.domain.pk}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Domain name is converted to uppercase slug
        self.assertEqual(response.json()['name'], 'UPDATED-DOMAIN')

    def test_delete_domain(self):
        domain = Domain.objects.create(name='ToDelete')
        response = self.client.delete(reverse('domain-detail', kwargs={'pk': domain.pk}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Domain.objects.filter(pk=domain.pk).exists())


class TestScopeViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='admin', email='admin@test.com', password='admin', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.property_att = Property.objects.create(name='Test Property', prefix='TST')
        self.attribute = Attribute.objects.create(property_att=self.property_att, value='value1')

        self.domain = Domain.objects.create(name='Test Domain')

        self.scope = Scope.objects.create(name='Test Scope', domain=self.domain, user=self.user)
        self.scope.included_attributes.add(self.attribute)

    def test_list_scopes(self):
        response = self.client.get(reverse('scope-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)

    def test_retrieve_scope(self):
        response = self.client.get(reverse('scope-detail', kwargs={'pk': self.scope.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], self.scope.name)

    def test_create_scope(self):
        data = {
            'name': 'New Scope',
            'domain': self.domain.pk,
            'user': self.user.pk,
            'included_attributes': [self.attribute.pk],
            'excluded_attributes': [],
        }
        response = self.client.post(reverse('scope-list'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Name is converted to slug
        self.assertEqual(response.json()['name'], 'new-scope')

    def test_update_scope(self):
        data = {'name': 'Updated Scope', 'domain': self.domain.pk, 'user': self.user.pk}
        response = self.client.patch(reverse('scope-detail', kwargs={'pk': self.scope.pk}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Name is converted to slug
        self.assertEqual(response.json()['name'], 'updated-scope')

    def test_delete_scope(self):
        scope = Scope.objects.create(name='ToDelete', domain=self.domain, user=self.user)
        response = self.client.delete(reverse('scope-detail', kwargs={'pk': scope.pk}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Scope.objects.filter(pk=scope.pk).exists())
