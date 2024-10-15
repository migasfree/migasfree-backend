import pytest

from django.test import TestCase

from migasfree.core.models import Attribute, Property


@pytest.fixture
def property_att():
    return Property.objects.create(name='some_property')


@pytest.mark.django_db
def test_create_attributes(property_att):
    value = 'attr1, attr2, attr3\n, attr4'

    attributes_ids = Attribute._kind_list(property_att, value)

    assert len(attributes_ids) == 4
    assert all(Attribute.objects.filter(id=attr_id).exists() for attr_id in attributes_ids)


@pytest.mark.django_db
def test_kind_list_empty_value(property_att):
    value = ''

    result = Attribute._kind_list(property_att, value)

    assert len(result) == 0


@pytest.mark.django_db
def test_kind_list_whitespace_value(property_att):
    value = '   '

    result = Attribute._kind_list(property_att, value)

    assert len(result) == 0


@pytest.mark.django_db
def test_kind_list_newline_value(property_att):
    value = 'value1\nvalue2'

    result = Attribute._kind_list(property_att, value)

    assert len(result) == 1
    assert Attribute.objects.filter(property_att=property_att, value=value).exists()


@pytest.mark.django_db
def test_kind_by_side_server():
    property_att = Property.objects.create(name='test', sort='server', kind='R')
    value = 'hello.world'

    attributes = Attribute._kind_by_side(property_att, value)

    assert len(attributes) == 3
    assert Attribute.objects.filter(property_att=property_att, value='').exists()
    assert Attribute.objects.filter(property_att=property_att, value='world').exists()
    assert Attribute.objects.filter(property_att=property_att, value='hello.world').exists()


@pytest.mark.django_db
def test_kind_by_side_right():
    property_att = Property.objects.create(name='test', sort='client', kind='R')
    value = 'hello.world.foo.bar'

    attributes = Attribute._kind_by_side(property_att, value)

    assert len(attributes) == 4
    assert Attribute.objects.filter(property_att=property_att, value='hello.world.foo.bar').exists()
    assert Attribute.objects.filter(property_att=property_att, value='world.foo.bar').exists()
    assert Attribute.objects.filter(property_att=property_att, value='foo.bar').exists()
    assert Attribute.objects.filter(property_att=property_att, value='bar').exists()


@pytest.mark.django_db
def test_kind_by_side_left():
    property_att = Property.objects.create(name='test', sort='client', kind='L')
    value = 'hello.world.foo.bar'

    attributes = Attribute._kind_by_side(property_att, value)

    assert len(attributes) == 4
    assert Attribute.objects.filter(property_att=property_att, value='hello').exists()
    assert Attribute.objects.filter(property_att=property_att, value='hello.world').exists()
    assert Attribute.objects.filter(property_att=property_att, value='hello.world.foo').exists()
    assert Attribute.objects.filter(property_att=property_att, value='hello.world.foo.bar').exists()


class TestAttribute(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.property_att = Property.objects.create(name='test', sort='client', kind='N')
        cls.value = 'proof value'

    def test_process_kind_property_normal(self):
        self.property_att.kind = 'N'
        result = Attribute.process_kind_property(self.property_att, self.value)

        assert result == Attribute._kind_normal(self.property_att, self.value)

    def test_process_kind_property_list(self):
        self.property_att.kind = '-'
        result = Attribute.process_kind_property(self.property_att, self.value)
        assert result == Attribute._kind_list(self.property_att, self.value)

    def test_process_kind_property_by_side(self):
        self.property_att.kind = 'R'
        result = Attribute.process_kind_property(self.property_att, self.value)
        assert result == Attribute._kind_by_side(self.property_att, self.value)

        self.property_att.kind = 'L'
        result = Attribute.process_kind_property(self.property_att, self.value)
        assert result == Attribute._kind_by_side(self.property_att, self.value)

    def test_process_kind_property_json(self):
        self.property_att.kind = 'J'
        result = Attribute.process_kind_property(self.property_att, self.value)
        assert result == Attribute._kind_json(self.property_att, self.value)

    def test_process_kind_property_invalid_kind(self):
        self.property_att.kind = 'X'
        result = Attribute.process_kind_property(self.property_att, self.value)
        assert result == []

    def test_process_kind_property_none_kind(self):
        self.property_att.kind = None
        result = Attribute.process_kind_property(self.property_att, self.value)
        assert result == []

    def test_process_kind_property_empty_kind(self):
        self.property_att.kind = ''
        result = Attribute.process_kind_property(self.property_att, self.value)
        assert result == []
