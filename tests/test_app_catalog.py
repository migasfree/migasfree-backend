import uuid

from django.test import TestCase

from migasfree.app_catalog.models import Application, Category, Policy, PolicyGroup
from migasfree.client.models import Computer
from migasfree.core.models import Attribute, Package, Platform, Project, Property, Store


class TestApplicationModel(TestCase):
    def setUp(self):
        self.platform = Platform.objects.create('Linux')
        self.project = Project.objects.create(
            name='Vitalinux', platform=self.platform, pms='apt', architecture='amd64'
        )

        self.category1 = Category.objects.create(name='Cat1')
        self.category2 = Category.objects.create(name='Cat2')

        self.application1 = Application.objects.create(name='App1', category=self.category1, level='U')
        self.application2 = Application.objects.create(name='App2', category=self.category1, level='U')
        self.application3 = Application.objects.create(name='App3', category=self.category2, level='A')

    def test_group_by_category(self):
        result = Application.group_by_category()
        expected = [
            {'category__id': 1, 'category__name': 'Cat1', 'count': 2},
            {'category__id': 2, 'category__name': 'Cat2', 'count': 1}
        ]

        self.assertEqual(list(result), expected)

    def test_group_by_level(self):
        result = Application.group_by_level()
        expected = [
            {'level': 'U', 'count': 2},
            {'level': 'A', 'count': 1}
        ]

        self.assertEqual(list(result), expected)

    def test_group_by_project(self):
        result = Application.group_by_project()
        expected = [
            {
                'packages_by_project__project__name': None,
                'packages_by_project__project__id': None,
                'count': 3
            },
        ]

        self.assertEqual(list(result), expected)


class TestPolicyModel(TestCase):
    def setUp(self):
        self.policy = Policy.objects.create(name='Proof', enabled=True)
        self.policy_group = PolicyGroup.objects.create(policy=self.policy, priority=1)

        self.platform = Platform.objects.create('Linux')
        self.project = Project.objects.create(
            name='Vitalinux', platform=self.platform, pms='apt', architecture='amd64'
        )

        self.property_att = Property.objects.create(name='Prop1', prefix='PRO')

    def test_belongs(self):
        attribute1 = Attribute.objects.create(property_att=self.property_att, value='one')
        attribute2 = Attribute.objects.create(property_att=self.property_att, value='two')

        computer = Computer.objects.create(project=self.project, name='PC1', uuid=str(uuid.uuid4()))
        computer.sync_attributes.set([attribute1.id, attribute2.id])

        self.assertTrue(Policy.belongs(computer, [attribute1, attribute2]))
        self.assertTrue(Policy.belongs(computer, [attribute1]))

    def test_belongs_excluding(self):
        included_attribute = Attribute.objects.create(property_att=self.property_att, value='one')
        excluded_attribute = Attribute.objects.create(property_att=self.property_att, value='two')

        computer = Computer.objects.create(project=self.project, name='PC1', uuid=str(uuid.uuid4()))
        computer.sync_attributes.set([included_attribute.id])

        policy = Policy.objects.create(name='Proof2', enabled=True)
        policy.included_attributes.add(included_attribute)
        policy.excluded_attributes.add(excluded_attribute)

        self.assertTrue(Policy.belongs_excluding(computer, [included_attribute], [excluded_attribute]))
        self.assertFalse(Policy.belongs_excluding(computer, [included_attribute], [included_attribute]))

    def test_get_packages_to_remove(self):
        policy = Policy.objects.create(name='Proof3', enabled=True)
        policy.exclusive = True
        policy.save()

        category = Category.objects.create(name='Cat1')
        application1 = Application.objects.create(name='App1', category=category)
        application2 = Application.objects.create(name='App2', category=category)

        store = Store.objects.create(name='Store1', project=self.project)

        package1 = Package.objects.create(
            project=self.project, store=store,
            fullname='migasfree-package_1.0_amd64.deb',
            name='migasfree-package', version='1.0', architecture='amd64'
        )

        package2 = Package.objects.create(
            project=self.project, store=store,
            fullname='migasfree-other-package_1.0_amd64.deb',
            name='migasfree-other-package', version='1.0', architecture='amd64'
        )

        policy_group = PolicyGroup.objects.create(policy=policy, priority=1)
        policy_group.applications.add(application1)
        policy_group.applications.add(application2)

        application1.packages_by_project.create(project=self.project, packages_to_install=[package1])
        self.assertEqual(Policy.get_packages_to_remove(policy_group, self.project.id), [])

        application2.packages_by_project.create(project=self.project, packages_to_install=[package2])
        self.assertEqual(len(Policy.get_packages_to_remove(policy_group, self.project.id)), 0)

    def test_get_packages(self):
        included_attribute = Attribute.objects.create(property_att=self.property_att, value='one')

        policy = Policy.objects.create(name='Proof4', enabled=True, exclusive=True)
        policy.included_attributes.add(included_attribute)

        store = Store.objects.create(name='Store1', project=self.project)

        package1 = Package.objects.create(
            project=self.project, store=store,
            fullname='migasfree-package_1.0_amd64.deb',
            name='migasfree-package', version='1.0', architecture='amd64'
        )

        category = Category.objects.create(name='Cat1')
        application1 = Application.objects.create(name='App1', category=category)
        application1.packages_by_project.create(project=self.project, packages_to_install=[package1])

        policy_group = PolicyGroup.objects.create(policy=policy, priority=1)
        policy_group.applications.add(application1)

        computer = Computer.objects.create(project=self.project, name='PC1', uuid=str(uuid.uuid4()))
        computer.sync_attributes.set([included_attribute.id])

        to_install, to_remove = Policy.get_packages(computer)
        self.assertEqual(len(to_install), 0)
        self.assertEqual(len(to_remove), 0)
