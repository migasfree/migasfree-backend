import pytest

from migasfree.core.models import Package, Project, Platform, Store, UserProfile


def test_normalized_name_convention():
    package_name = "migasfree-package"
    name, version, architecture = Package.normalized_name(package_name)

    assert name is None
    assert version is None
    assert architecture == ''


def test_normalized_name_with_version():
    package_name = "migasfree-package_1.2.3"
    name, version, architecture = Package.normalized_name(package_name)

    assert name is None
    assert version is None
    assert architecture == ''


def test_normalized_name_with_architecture():
    package_name = "migasfree-package_1.2.3_amd64"
    name, version, architecture = Package.normalized_name(package_name)

    assert name == "migasfree-package"
    assert version == "1.2.3"
    assert architecture == "amd64"


def test_normalized_name_with_version_and_architecture():
    package_name = "migasfree-package_1.2.3_amd64.deb"
    name, version, architecture = Package.normalized_name(package_name)

    assert name == "migasfree-package"
    assert version == "1.2.3"
    assert architecture == "amd64"


def test_normalized_name_with_extra_slices():
    package_name = "migasfree-package_1.2.3_amd64.deb.tar.gz"
    name, version, architecture = Package.normalized_name(package_name)

    assert name == "migasfree-package"
    assert version == "1.2.3"
    assert architecture == "amd64"


def test_normalized_name_with_empty_architecture():
    package_name = "migasfree-package_1.2.3_"
    name, version, architecture = Package.normalized_name(package_name)

    assert name == "migasfree-package"
    assert version == "1.2.3"
    assert architecture == ''


@pytest.mark.django_db
def test_by_store_without_packages():
    user = UserProfile.objects.create_user('test', 'test@example.com', 'test')

    result = Package.by_store(user)

    assert result['total'] == 0
    assert result['inner'] == []
    assert result['outer'] == []


@pytest.mark.django_db
def test_by_store_with_packages():
    user = UserProfile.objects.create_user('test', 'test@example.com', 'test')

    platform = Platform.objects.create(name='Linux')
    project = Project.objects.create(name='Project 1', platform=platform, pms='apt', architecture='amd64')

    store = Store.objects.create(name='Store 1', project=project)

    Package.objects.create(
        project=project, store=store,
        fullname='migasfree-package_1.0_amd64.deb',
        name='migasfree-package', version='1.0', architecture='amd64'
    )

    result = Package.by_store(user)

    assert result['total'] == 1
    assert len(result['inner']) == 1
    assert result['inner'][0]['project__id'] == project.id
    assert result['inner'][0]['project__name'] == project.name
    assert result['inner'][0]['count'] == 1
    assert len(result['outer']) == 1
    assert result['outer'][0]['project__id'] == project.id
    assert result['outer'][0]['store__id'] == store.id
    assert result['outer'][0]['store__name'] == store.name
    assert result['outer'][0]['count'] == 1
