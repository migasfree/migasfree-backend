import pytest

from django.core.exceptions import ValidationError

from migasfree.core.models import AttributeSet, Property


@pytest.fixture
def property_att():
    return Property.objects.create(
        prefix='SET',
        name='Attribute Set',
        enabled=True,
        kind='N',
        sort='basic',
        language=1,
        code="print 'All Systems'"
    )


@pytest.mark.django_db
def test_sets_dependencies_empty():
    assert AttributeSet.objects.filter(enabled=True).count() == 0
    assert AttributeSet.sets_dependencies() == {}


@pytest.mark.django_db
def test_sets_dependencies_single_set(property_att):
    attribute_set = AttributeSet.objects.create(name='Test Set', enabled=True)

    assert AttributeSet.sets_dependencies() == {attribute_set.id: []}


@pytest.mark.django_db
def test_sets_dependencies_multiple_sets(property_att):
    attribute_set1 = AttributeSet.objects.create(name='Test Set 1', enabled=True)
    attribute_set2 = AttributeSet.objects.create(name='Test Set 2', enabled=True)
    attribute_set3 = AttributeSet.objects.create(name='Test Set 3', enabled=True)

    attribute_set1.included_attributes.create(value='Test Set 2', property_att=property_att)
    attribute_set2.included_attributes.create(value='Test Set 3', property_att=property_att)

    expected_dependencies = {
        attribute_set1.id: [attribute_set2.id],
        attribute_set2.id: [attribute_set3.id],
        attribute_set3.id: []
    }
    assert AttributeSet.sets_dependencies() == expected_dependencies


@pytest.mark.django_db
def test_sets_dependencies_all_systems_ignored(property_att):
    attribute_set = AttributeSet.objects.create(name='All Systems', enabled=True)

    assert AttributeSet.sets_dependencies() == {attribute_set.id: []}


@pytest.mark.django_db
def test_sets_dependencies_circular_dependencies(property_att):
    attribute_set1 = AttributeSet.objects.create(name='Test Set 1', enabled=True)
    attribute_set2 = AttributeSet.objects.create(name='Test Set 2', enabled=True)

    attribute_set1.included_attributes.create(value='Test Set 2', property_att=property_att)

    with pytest.raises(ValidationError):
        attribute_set2.included_attributes.create(value='Test Set 1', property_att=property_att)
