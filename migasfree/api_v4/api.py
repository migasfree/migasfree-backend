# -*- coding: utf-8 -*-

import os
import inspect
import logging

from datetime import datetime, timedelta

from django.db.models import Q
from django.conf import settings
from django.contrib import auth
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext as _

from ..app_catalog.models import Policy

from ..core.models import (
    Attribute, AttributeSet, BasicAttribute, Package, Platform, Property,
    Deployment, Store, ServerAttribute, Project, Domain, PackageSet,
)
from ..client.models import (
    Computer, Error, Fault, FaultDefinition, Notification,
    Synchronization, User,
)
from ..hardware.models import Node
from ..client.views.safe import (
    add_computer_message, remove_computer_messages, is_computer_changed,
)
from .secure import get_keys_to_client, get_keys_to_packager
from ..client.tasks import update_software_inventory
from ..hardware.tasks import save_computer_hardware
from ..core.pms.tasks import create_repository_metadata, package_metadata
from ..utils import (
    uuid_change_format, get_client_ip,
    list_difference, list_common, to_list,
    remove_duplicates_preserving_order, replace_keys,
    save_tempfile,
)
from . import errmfs

logger = logging.getLogger('migasfree')


def add_notification_platform(platform, computer):
    Notification.objects.create(
        _("Platform [%s] registered by computer [%s].") % (platform, computer)
    )


def add_notification_project(project, pms, computer):
    Notification.objects.create(
        _("Project [%s] with P.M.S. [%s] registered by computer [%s].") % (
            project, pms, computer
        )
    )


def get_computer(name, uuid):
    """
    Returns a computer object (or None if not found)
    """
    logger.debug('name: %s, uuid: %s', name, uuid)
    computer = None

    try:
        computer = Computer.objects.get(uuid=uuid)
        logger.debug('computer found by uuid')

        return computer
    except Computer.DoesNotExist:
        pass

    try:  # search with endian format changed
        computer = Computer.objects.get(uuid=uuid_change_format(uuid))
        logger.debug('computer found by uuid (endian format changed)')

        return computer
    except Computer.DoesNotExist:
        pass

    computer = Computer.objects.filter(mac_address__icontains=uuid[-12:])
    if computer.count() == 1 and uuid[0:8] == '0'*8:
        logger.debug('computer found by mac_address (in uuid format)')

        return computer.first()

    computer = None  # reset result to continue searching

    # DEPRECATED This Block. Only for compatibility with client <= 2
    message = 'computer found by name. compatibility mode'
    if len(uuid.split("-")) == 5:  # search for uuid (client >= 3)
        try:
            computer = Computer.objects.get(uuid=name)
            logger.debug(message)

            return computer
        except Computer.DoesNotExist:
            pass
    else:
        try:
            # search for name (client <= 2)
            computer = Computer.objects.get(name=name, uuid=name)
            logger.debug(message)

            return computer
        except Computer.DoesNotExist:
            try:
                computer = Computer.objects.get(name=name)
                logger.debug(message)

                return computer
            except (Computer.DoesNotExist, Computer.MultipleObjectsReturned):
                pass

    if computer is None:
        logger.debug('computer not found!!!')

    return computer


def upload_computer_hardware(request, name, uuid, computer, data):
    cmd = str(inspect.getframeinfo(inspect.currentframe()).function)

    hw_data = data[cmd]
    if isinstance(hw_data, list):
        hw_data = hw_data[0]

    try:
        Node.objects.filter(computer=computer).delete()
        save_computer_hardware.delay(computer.id, hw_data)
        computer.update_last_hardware_capture()
        computer.update_hardware_resume()
        ret = return_message(cmd, errmfs.ok())
    except IndexError:
        ret = return_message(cmd, errmfs.error(errmfs.GENERIC))

    return ret


def upload_computer_software_base_diff(request, name, uuid, computer, data):
    cmd = str(inspect.getframeinfo(inspect.currentframe()).function)
    try:
        packages = data[cmd].split('\n')
        clean_packages = [i[1:] for i in packages]
        update_software_inventory.delay(computer.id, clean_packages)
        ret = return_message(cmd, errmfs.ok())
    except IndexError:
        ret = return_message(cmd, errmfs.error(errmfs.GENERIC))

    return ret


def upload_computer_software_base(request, name, uuid, computer, data):
    """ DEPRECATED endpoint for migasfree-client >= 4.14 """
    cmd = str(inspect.getframeinfo(inspect.currentframe()).function)
    return return_message(cmd, errmfs.ok())


def upload_computer_software_history(request, name, uuid, computer, data):
    cmd = str(inspect.getframeinfo(inspect.currentframe()).function)
    try:
        computer.update_software_history(data[cmd])
        ret = return_message(cmd, errmfs.ok())
    except IndexError:
        ret = return_message(cmd, errmfs.error(errmfs.GENERIC))

    return ret


def get_computer_software(request, name, uuid, computer, data):
    """ DEPRECATED endpoint for migasfree-client >= 4.14 """
    cmd = str(inspect.getframeinfo(inspect.currentframe()).function)

    return return_message(
        cmd,
        ''  # deprecated field computer.version.base, empty for compatibility!!!
    )


def upload_computer_errors(request, name, uuid, computer, data):
    cmd = str(inspect.getframeinfo(inspect.currentframe()).function)
    try:
        Error.objects.create(computer, computer.project, data[cmd])

        ret = return_message(cmd, errmfs.ok())
    except IndexError:
        ret = return_message(cmd, errmfs.error(errmfs.GENERIC))

    return ret


def upload_computer_message(request, name, uuid, computer, data):
    cmd = str(inspect.getframeinfo(inspect.currentframe()).function)

    if not computer:
        return return_message(cmd, errmfs.error(errmfs.COMPUTER_NOT_FOUND))

    if data.get(cmd, '') == '':
        remove_computer_messages(computer.id)
        Synchronization.objects.create(
            computer,
            consumer='migasfree_4.x',
            start_date=computer.sync_start_date
        )
    else:
        add_computer_message(computer, data.get(cmd, ''))

    ret = return_message(cmd, errmfs.ok())

    return ret


def return_message(cmd, data):
    return {f'{cmd}.return': data}


def get_properties(request, name, uuid, computer, data):
    """
    First call of client requesting to server what it must do.
    The server responds a JSON:

        OUTPUT:
        ======
            {
                "properties":
                    [
                        {
                            "name": "PREFIX",
                            "code": "CODE" ,
                            "language": "LANGUAGE"
                        },
                        ...
                    ],
            }

    The client will eval the code in PROPERTIES and FAULTS and
    will upload it to server in a file called request.json
    calling to "post_request" view
    """

    return return_message(
        str(inspect.getframeinfo(inspect.currentframe()).function),
        {
            'properties': replace_keys(
                Property.enabled_client_properties(
                    computer.get_all_attributes()
                ),
                {'prefix': 'name', 'language': 'language', 'code': 'code'}
            )
        }
    )


def upload_computer_info(request, name, uuid, computer, data):
    """
    Process the file request.json and returns a JSON with:
        * fault definitions
        * repositories
        * packages
        * devices

        INPUT:
        =====
        A file "request.json" with the result of evaluate the request obtained
        by "get_request"

            {
                "computer": {
                    "hostname": HOSTNAME,
                    ["fqdn": FQDN,]
                    "ip": IP,
                    "platform": PLATFORM,
                    "version" | "project": VERSION/PROJECT,
                    "user": USER,
                    "user_fullname": USER_FULLNAME
                },
                "attributes":[{"name": VALUE}, ...]
            }

        OUTPUT:
        ======
        After of process this file, the server responds to client a JSON:

            {
                "faultsdef": [
                    {
                        "name": "NAME",
                        "code": "CODE",
                        "language": "LANGUAGE"
                    },
                    ...
                ],
                "repositories": [ {"name": "REPONAME", "source_template": "template" }, ...],
                "packages": {
                    "install": ["pkg1","pkg2","pkg3", ...],
                    "remove": ["pkg1","pkg2","pkg3", ...]
                } ,
                "base": true|false,
                "hardware_capture": true|false,
                "devices": {
                    "logical": [object1, object2, ...],
                    "default": int
                }
            }
    """

    cmd = str(inspect.getframeinfo(inspect.currentframe()).function)

    computer_info = data.get(cmd).get('computer')
    platform_name = computer_info.get('platform', 'unknown')
    project_name = computer_info.get(
        'version',  # key is version for compatibility!!!
        computer_info.get('project', 'unknown')
    )
    pms_name = computer_info.get('pms', 'apt')
    fqdn = computer_info.get('fqdn', None)

    if pms_name.startswith('apt'):  # normalize PMS name in v5
        pms_name = 'apt'

    notify_platform = False
    notify_project = False

    # auto register Platform
    if not Platform.objects.filter(name=platform_name).exists():
        if not settings.MIGASFREE_AUTOREGISTER:
            return return_message(
                cmd,
                errmfs.error(errmfs.CAN_NOT_REGISTER_COMPUTER)
            )

        # if all ok we add the platform
        Platform.objects.create(platform_name)

        notify_platform = True

    # auto register project
    if not Project.objects.filter(name=project_name).exists():
        if not settings.MIGASFREE_AUTOREGISTER:
            return return_message(
                cmd,
                errmfs.error(errmfs.CAN_NOT_REGISTER_COMPUTER)
            )

        # if all ok, we add the project
        Project.objects.create(
            name=project_name,
            pms=pms_name,
            architecture='amd64',
            platform=Platform.objects.get(name=platform_name),
            auto_register_computers=settings.MIGASFREE_AUTOREGISTER
        )

        notify_project = True

    try:
        client_attributes = data.get(cmd).get("attributes")  # basic and client attributes
        ip_address = computer_info.get("ip", "")
        forwarded_ip_address = get_client_ip(request)

        # IP registration, project and computer Migration
        is_computer_changed(
            computer,
            name,
            Project.objects.get(name=project_name),
            ip_address,
            uuid
        )
        if computer:
            computer.update_identification(
                name, fqdn, Project.objects.get(name=project_name), uuid,
                ip_address, forwarded_ip_address
            )

        project = Project.objects.get(name=project_name)

        if notify_platform:
            platform = Platform.objects.get(name=platform_name)
            add_notification_platform(platform, computer)

        if notify_project:
            add_notification_project(project, pms_name, computer)

        # if not exists the user, we add it
        user_fullname = computer_info.get('user_fullname', '')
        user, _ = User.objects.get_or_create(
            name=computer_info.get('user'),
            defaults={
                'fullname': user_fullname
            }
        )
        user.update_fullname(user_fullname)

        computer.update_sync_user(user)
        computer.sync_attributes.clear()

        # basic attributes
        computer.sync_attributes.add(
            *BasicAttribute.process(
                id=computer.id,
                ip_address=ip_address,
                project=computer.project.name,
                platform=computer.project.platform.name,
                user=user.name,
                description=computer.get_cid_description()
            )
        )

        # client attributes
        for prefix, value in client_attributes.items():
            client_property = Property.objects.get(prefix=prefix)
            if client_property.sort == 'client':
                computer.sync_attributes.add(
                    *Attribute.process_kind_property(client_property, value)
                )

        # Domain attribute
        computer.sync_attributes.add(*Domain.process(computer.get_all_attributes()))

        # Tags (server attributes) (not running on clients!!!)
        for tag in computer.tags.filter(property_att__enabled=True):
            computer.sync_attributes.add(
                *Attribute.process_kind_property(tag.property_att, tag.value)
            )

        # AttributeSets
        computer.sync_attributes.add(*AttributeSet.process(computer.get_all_attributes()))

        results = FaultDefinition.enabled_for_attributes(computer.get_all_attributes())
        fault_definitions = []
        for item in results:
            fault_definitions.append({
                'language': item.get_language_display(),
                'name': item.name,
                'code': item.code
            })

        lst_deploys = []
        lst_pkg_to_remove = []
        lst_pkg_to_install = []

        # deployments
        deploys = Deployment.available_deployments(computer, computer.get_all_attributes())
        for dep in deploys:
            lst_deploys.append({'name': dep.name, 'source_template': dep.source_template()})

            if dep.packages_to_remove:
                for pkg in to_list(dep.packages_to_remove):
                    if pkg != "":
                        lst_pkg_to_remove.append(pkg)

            if dep.packages_to_install:
                for pkg in to_list(dep.packages_to_install):
                    if pkg != "":
                        lst_pkg_to_install.append(pkg)

        # policies
        policy_pkg_to_install, policy_pkg_to_remove = Policy.get_packages(computer)
        lst_pkg_to_install.extend([x['package'] for x in policy_pkg_to_install])
        lst_pkg_to_remove.extend([x['package'] for x in policy_pkg_to_remove])

        # devices
        logical_devices = []
        for device in computer.logical_devices(computer.get_all_attributes()):
            logical_devices.append(device.as_dict(computer.project))

        default_logical_device = 0
        if computer.default_logical_device:
            default_logical_device = computer.default_logical_device.id

        # Hardware
        capture_hardware = True
        if computer.last_hardware_capture:
            capture_hardware = (datetime.now() > (
                computer.last_hardware_capture.replace(tzinfo=None) + timedelta(
                    days=settings.MIGASFREE_HW_PERIOD
                ))
            )

        # Finally, JSON creation
        data = {
            "faultsdef": fault_definitions,
            "repositories": lst_deploys,
            "packages": {
                "remove": remove_duplicates_preserving_order(lst_pkg_to_remove),
                "install": remove_duplicates_preserving_order(lst_pkg_to_install)
            },
            "devices": {
                "logical": logical_devices,
                "default": default_logical_device,
            },
            "base": False,  # computerbase and base has been removed!!!
            "hardware_capture": capture_hardware
        }

        ret = return_message(cmd, data)
    except ObjectDoesNotExist:
        ret = return_message(cmd, errmfs.error(errmfs.GENERIC))

    return ret


def upload_computer_faults(request, name, uuid, computer, data):
    """
    INPUT:
        'faults': {
            'name': 'result',
            ...
        }
    """

    cmd = str(inspect.getframeinfo(inspect.currentframe()).function)
    faults = data.get(cmd).get("faults")

    try:
        for fault_name, result in faults.items():
            try:
                if result:  # something went wrong
                    Fault.objects.create(
                        computer,
                        FaultDefinition.objects.get(name=fault_name),
                        result
                    )
            except ObjectDoesNotExist:
                pass

        ret = return_message(cmd, {})
    except AttributeError:
        ret = return_message(cmd, errmfs.error(errmfs.GENERIC))

    logger.debug('upload_computer_faults ret: %s', ret)
    return ret


def upload_devices_changes(request, name, uuid, computer, data):
    """ DEPRECATED endpoint for migasfree-client >= 4.13 """
    logger.debug('upload_devices_changes data: %s', data)
    cmd = str(inspect.getframeinfo(inspect.currentframe()).function)

    return return_message(cmd, errmfs.ok())


def register_computer(request, name, uuid, computer, data):
    cmd = str(inspect.getframeinfo(inspect.currentframe()).function)

    user = auth.authenticate(
        username=data.get('username'),
        password=data.get('password')
    )

    platform_name = data.get('platform', 'unknown')
    project_name = data.get('version', data.get('project', 'unknown'))  # key is version for compatibility!!!
    pms_name = data.get('pms', 'apt')
    fqdn = data.get('fqdn', None)

    if pms_name.startswith('apt'):  # normalize PMS name in v5
        pms_name = 'apt'

    notify_platform = False
    notify_project = False

    # auto register Platform
    if not Platform.objects.filter(name=platform_name).exists():
        if not settings.MIGASFREE_AUTOREGISTER:
            if not user or not user.has_perm('core.add_platform'):
                return return_message(
                    cmd,
                    errmfs.error(errmfs.CAN_NOT_REGISTER_COMPUTER)
                )

        # if all ok we add the platform
        Platform.objects.create(platform_name)

        notify_platform = True

    # auto register project
    if not Project.objects.filter(name=project_name).exists():
        if not settings.MIGASFREE_AUTOREGISTER:
            if not user or not user.has_perm('core.add_project'):
                return return_message(
                    cmd,
                    errmfs.error(errmfs.CAN_NOT_REGISTER_COMPUTER)
                )

        # if all ok we add the project
        Project.objects.create(
            name=project_name,
            pms=pms_name,
            architecture='amd64',  # by default
            platform=Platform.objects.get(name=platform_name),
            auto_register_computers=settings.MIGASFREE_AUTOREGISTER
        )

        notify_project = True

    # REGISTER COMPUTER
    # Check project
    try:
        project = Project.objects.get(name=project_name)
        # if not auto register, check that user can save computer
        if not project.auto_register_computers:
            if not user or not user.has_perm("client.add_computer") \
                    or not user.has_perm("client.change_computer"):
                return return_message(
                    cmd,
                    errmfs.error(errmfs.CAN_NOT_REGISTER_COMPUTER)
                )

        # Add Computer
        is_computer_changed(
            computer,
            name,
            Project.objects.get(name=project_name),
            data.get('ip', ''),
            uuid
        )
        if computer:
            computer.update_identification(
                name, fqdn, Project.objects.get(name=project_name),
                uuid, data.get('ip', ''), get_client_ip(request)
            )

        if notify_platform:
            platform = Platform.objects.get(name=platform_name)
            add_notification_platform(platform, computer)

        if notify_project:
            add_notification_project(project, pms_name, computer)

        # Add Computer to Domain
        if user and user.userprofile.domain_preference:
            user.userprofile.domain_preference.included_attributes.add(
                computer.get_cid_attribute()
            )

        # returns keys to client
        return return_message(cmd, get_keys_to_client(project_name))
    except ObjectDoesNotExist:
        return return_message(
            cmd,
            errmfs.error(errmfs.USER_DOES_NOT_HAVE_PERMISSION)
        )


def get_key_packager(request, name, uuid, computer, data):
    cmd = str(inspect.getframeinfo(inspect.currentframe()).function)
    user = auth.authenticate(
        username=data['username'],
        password=data['password']
    )
    if not user or not user.has_perm("core.add_package") \
            or not user.has_perm("core.change_package"):
        return return_message(
            cmd,
            errmfs.error(errmfs.CAN_NOT_REGISTER_COMPUTER)
        )

    return return_message(cmd, get_keys_to_packager())


def get_package_data(_file, project):
    name, version, architecture = Package.normalized_name(_file.name)
    if not name:
        package_path = save_tempfile(_file)
        response = package_metadata.apply_async(
            kwargs={
                'pms_name': project.pms,
                'package': package_path
            },
            queue=f'pms-{project.pms}'
        ).get()
        os.remove(package_path)
        if response['name']:
            name = response['name']
            version = response['version']
            architecture = response['architecture']

    return name, version, architecture


def upload_server_package(request, name, uuid, computer, data):
    cmd = str(inspect.getframeinfo(inspect.currentframe()).function)

    project_name = data.get('version', data.get('project'))

    try:
        project = Project.objects.get(name=project_name)
    except ObjectDoesNotExist:
        return return_message(cmd, errmfs.error(errmfs.PROJECT_NOT_FOUND))

    store, _ = Store.objects.get_or_create(
        name=data['store'], project=project
    )

    _file = request.FILES["package"]

    package = Package.objects.filter(
        fullname=_file.name,
        project=project
    )
    name, version, architecture = get_package_data(_file, project)
    if package.exists():
        package[0].update_store(store)
        if name and version and architecture:
            package[0].update_package_data(name, version, architecture)
    else:
        Package.objects.create(
            fullname=_file.name,
            name=name,
            version=version,
            architecture=architecture,
            project=project,
            store=store,
            file_=_file
        )

    target = Package.path(project.slug, store.slug, _file.name)
    Package.handle_uploaded_file(_file, target)

    return return_message(cmd, errmfs.ok())


def upload_server_set(request, name, uuid, computer, data):
    cmd = str(inspect.getframeinfo(inspect.currentframe()).function)

    project_name = data.get('version', data.get('project'))
    _file = request.FILES["package"]

    try:
        project = Project.objects.get(name=project_name)
    except ObjectDoesNotExist:
        return return_message(cmd, errmfs.error(errmfs.PROJECT_NOT_FOUND))

    store, _ = Store.objects.get_or_create(
        name=data['store'], project=project
    )

    package_set = PackageSet.objects.filter(name=data['packageset'], project=project).first()
    if package_set:
        package_set.update_store(store)
    else:
        package_set = PackageSet.objects.create(
            name=data['packageset'],
            project=project,
            store=store,
        )

    package = Package.objects.filter(fullname=_file, project=project).first()
    name, version, architecture = get_package_data(_file, project)
    if package:
        package.update_store(store)
        if name and version and architecture:
            package.update_package_data(name, version, architecture)
    else:
        package = Package.objects.create(
            fullname=_file.name,
            name=name,
            version=version,
            architecture=architecture,
            project=project,
            store=store,
            file_=_file
        )

    target = Package.path(project.slug, store.slug, _file.name)
    Package.handle_uploaded_file(_file, target)

    # if exists path, move it
    if "path" in data and data["path"] != "":
        dst = os.path.join(
            Store.path(project.slug, store.slug),
            data['path'],
            _file.name
        )
        try:
            os.makedirs(os.path.dirname(dst))
        except OSError:
            pass
        os.rename(target, dst)

    package_set.packages.add(package.id)

    return return_message(cmd, errmfs.ok())


def get_computer_tags(request, name, uuid, computer, data):
    cmd = str(inspect.getframeinfo(inspect.currentframe()).function)

    available_tags = {}
    selected_tags = []
    for tag in computer.tags.all():
        selected_tags.append(tag.__str__())

        # if tag is a domain, includes all domain's tags
        if tag.property_att.prefix == 'DMN':
            for tag_dmn in Domain.objects.get(name=tag.value.split('.')[0]).get_tags():
                available_tags.setdefault(tag_dmn.property_att.name, []).append(str(tag_dmn))

    # DEPLOYMENT TAGS
    for deploy in Deployment.objects.filter(
        project=computer.project,
        enabled=True
    ):
        for tag in deploy.included_attributes.filter(
            property_att__sort='server',
            property_att__enabled=True
        ):
            available_tags.setdefault(tag.property_att.name, []).append(str(tag))

    # DOMAIN TAGS
    for domain in Domain.objects.filter(
        Q(included_attributes__in=computer.sync_attributes.all()) &
        ~Q(excluded_attributes__in=computer.sync_attributes.all())
    ):
        for tag in domain.tags.all():
            available_tags.setdefault(tag.property_att.name, []).append(str(tag))

    ret = errmfs.ok()
    ret['available'] = available_tags
    ret['selected'] = selected_tags

    return return_message(cmd, ret)


def set_computer_tags(request, name, uuid, computer, data):
    cmd = str(inspect.getframeinfo(inspect.currentframe()).function)
    all_id = Attribute.objects.get(pk=1).id  # All Systems attribute is the first one

    try:
        lst_tags_obj = []
        lst_tags_id = []
        for tag in data["set_computer_tags"]["tags"]:
            ltag = tag.split("-", 1)
            if len(ltag) > 1:
                attribute = ServerAttribute.objects.get(
                    property_att__prefix=ltag[0],
                    value=ltag[1]
                )
                lst_tags_obj.append(attribute)
                lst_tags_id.append(attribute.id)
        lst_tags_id.append(all_id)

        lst_computer_id = list(computer.tags.values_list('id', flat=True))
        lst_computer_id.append(all_id)

        old_tags_id = list_difference(lst_computer_id, lst_tags_id)
        new_tags_id = list_difference(lst_tags_id, lst_computer_id)
        com_tags_id = list_common(lst_computer_id, lst_tags_id)

        lst_pkg_remove = []
        lst_pkg_install = []
        lst_pkg_preinstall = []

        # old deployments
        for deploy in Deployment.available_deployments(computer, old_tags_id):
            # INVERSE !!!!
            lst_pkg_remove.extend(
                to_list(
                    '{} {} {}'.format(
                        deploy.packages_to_install,
                        deploy.default_included_packages,
                        deploy.default_preincluded_packages
                    )
                )
            )

            lst_pkg_install.extend(
                to_list(f'{deploy.packages_to_remove} {deploy.default_excluded_packages}')
            )

        # new deployments
        for deploy in Deployment.available_deployments(
            computer,
            new_tags_id + com_tags_id
        ):
            lst_pkg_remove.extend(
                to_list(f'{deploy.packages_to_remove} {deploy.default_excluded_packages}')
            )

            lst_pkg_install.extend(
                to_list(f'{deploy.packages_to_install} {deploy.default_included_packages}')
            )

            lst_pkg_preinstall.extend(
                to_list(deploy.default_preincluded_packages)
            )

        ret_data = errmfs.ok()
        ret_data["packages"] = {
            "preinstall": lst_pkg_preinstall,
            "install": lst_pkg_install,
            "remove": lst_pkg_remove,
        }

        computer.tags.set(lst_tags_obj)

        ret = return_message(cmd, ret_data)
    except ObjectDoesNotExist:
        ret = return_message(cmd, errmfs.error(errmfs.GENERIC))

    return ret


def create_repositories_package(package_name, project_name):
    try:
        project = Project.objects.get(name=project_name)
        package = Package.objects.get(name=package_name, project=project)
        for deploy in Deployment.objects.filter(available_packages__id=package.id):
            create_repository_metadata.apply_async(
                queue=f'pms-{deploy.pms().name}',
                kwargs={'deployment_id': deploy.id}
            )
    except ObjectDoesNotExist:
        pass


def create_repositories_of_packageset(request, name, uuid, computer, data):
    cmd = str(inspect.getframeinfo(inspect.currentframe()).function)

    project_name = data.get('version', data.get('project'))

    try:
        create_repositories_package(
            os.path.basename(data['packageset']),
            project_name
        )
        ret = return_message(cmd, errmfs.ok())
    except KeyError:
        ret = return_message(cmd, errmfs.error(errmfs.GENERIC))

    return ret


def save_request_file(archive, target):
    with open(target, 'wb+') as _file:
        for chunk in archive.chunks():
            _file.write(chunk)

    try:
        # https://docs.djangoproject.com/en/dev/topics/http/file-uploads/
        # Files with: Size > FILE_UPLOAD_MAX_MEMORY_SIZE  -> generate a file
        # called something like /tmp/tmpzfp6I6.upload.
        # We remove it
        os.remove(archive.temporary_file_path())
    except (OSError, AttributeError):
        pass
