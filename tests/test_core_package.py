import pytest

from migasfree.core.models import Package, Project, Platform, Store, UserProfile


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


@pytest.mark.parametrize(
    'filename, expected',
    [
        ('migasfree-play_5.9-0_amd64.deb', ('migasfree-play', '5.9-0', 'amd64')),
        ('migasfree-play_5.9-0_x86_64.rpm', ('migasfree-play', '5.9-0', 'x86_64')),
        ('migasfree-play-5.9-0.x86_64.rpm', ('migasfree-play', '5.9-0', 'x86_64')),
        ('migasfree-client_5.0-1_any.pkg.tar.zst', ('migasfree-client', '5.0-1', 'any')),
        (
            'ca-certificates_2024.2.69_v8.0.401-1.0.fc40_noarch.rpm',
            ('ca-certificates', '2024.2.69_v8.0.401-1.0.fc40', 'noarch')
        ),
        ('a52dec_0.7.4-11_x86_64.pkg.tar.zst', ('a52dec', '0.7.4-11', 'x86_64')),
        ('migasfree-package', ('migasfree-package', '', '')),
        ('migasfree-package_1.2.3_amd64', ('migasfree-package', '1.2.3', 'amd64')),
    ],
)
def test_normalized_name(filename, expected):
    package = Package()
    result = package.normalized_name(filename)
    assert result == expected


def test_normalized_name_no_match():
    package = Package()
    result = package.normalized_name('no-match')
    assert result == ('no-match', '', '')
