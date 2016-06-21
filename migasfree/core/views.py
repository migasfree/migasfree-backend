# -*- coding: utf-8 *-*

# Copyright (c) 2015-2016 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2016 Alberto Gacías <alberto@migasfree.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os

from django.conf import settings
from django.shortcuts import get_object_or_404
# from django.core import signing
from django.utils.translation import ugettext, ugettext_lazy as _
# from django.contrib.auth.models import User, Group
from django_redis import get_redis_connection
from rest_framework import (
    viewsets, parsers, status, mixins,
    exceptions, filters
)
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework_filters import backends

from .mixins import SafeConnectionMixin

from .models import (
    Platform, Project, Store,
    ServerProperty, ClientProperty,
    ServerAttribute, ClientAttribute,
    Schedule,
    Package, Deployment,
)
from .serializers import (
    # UserSerializer, GroupSerializer,
    PlatformSerializer, ProjectSerializer, StoreSerializer,
    ServerPropertySerializer, ClientPropertySerializer,
    ServerAttributeSerializer, ClientAttributeSerializer,
    ScheduleSerializer,
    PackageSerializer, DeploymentSerializer,
)
from .filters import (
    DeploymentFilter, PackageFilter, ProjectFilter, StoreFilter,
    ClientAttributeFilter, ServerAttributeFilter,
)
from .permissions import IsAdminOrIsSelf

from . import tasks


class SafePackagerConnectionMixin(SafeConnectionMixin):
    decrypt_key = settings.MIGASFREE_PRIVATE_KEY
    verify_key = settings.MIGASFREE_PACKAGER_PUB_KEY

    sign_key = settings.MIGASFREE_PRIVATE_KEY
    encrypt_key = settings.MIGASFREE_PACKAGER_PUB_KEY

'''
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @detail_route(
        methods=['post'],
        permission_classes=[IsAdminOrIsSelf],
        url_path='change-password'
    )
    def set_password(self, request, pk=None):
        user = self.get_object()
        serializer = PasswordSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.data['password'])
            user.save()
            return Response({'status': 'password set'})
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

    @list_route(url_path='recent-users')
    def recent_users(self, request):
        recent_users = User.objects.all().order('-last_login')
        page = self.paginate_queryset(recent_users)
        serializer = self.get_pagination_serializer(page)
        return Response(serializer.data)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
'''


class PlatformViewSet(viewsets.ModelViewSet):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    filter_class = ProjectFilter
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend)


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    filter_class = StoreFilter
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend)


class ServerPropertyViewSet(viewsets.ModelViewSet):
    queryset = ServerProperty.objects.filter(sort='server')
    serializer_class = ServerPropertySerializer


class ClientPropertyViewSet(viewsets.ModelViewSet):
    queryset = ClientProperty.objects.filter(sort='client')
    serializer_class = ClientPropertySerializer


class ServerAttributeViewSet(viewsets.ModelViewSet):
    queryset = ServerAttribute.objects.filter(property_att__sort='server')
    serializer_class = ServerAttributeSerializer
    filter_class = ServerAttributeFilter
    paginate_by = 100  # FIXME constant


class ClientAttributeViewSet(viewsets.ModelViewSet):
    queryset = ClientAttribute.objects.filter(property_att__sort='client')
    serializer_class = ClientAttributeSerializer
    filter_class = ClientAttributeFilter
    paginate_by = 100  # FIXME constant


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer


class PackageViewSet(
        mixins.CreateModelMixin,
        mixins.RetrieveModelMixin,
        mixins.DestroyModelMixin,
        mixins.ListModelMixin,
        viewsets.GenericViewSet
):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    filter_class = PackageFilter
    parser_classes = (parsers.MultiPartParser, parsers.FormParser,)
    paginate_by = 100  # FIXME constant

    @list_route(methods=['get'])
    def orphaned(self, request):
        """
        Returns packages that are not in any deployment
        """
        serializer = PackageSerializer(
            Package.objects.filter(deployment__id=None),
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class DeploymentViewSet(viewsets.ModelViewSet):
    queryset = Deployment.objects.all()
    serializer_class = DeploymentSerializer
    filter_class = DeploymentFilter
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend)
    ordering_fields = '__all__'
    ordering = ('-start_date',)
    paginate_by = 100  # FIXME constant

    @detail_route(methods=['get'])
    def metadata(self, request, pk=None):
        get_object_or_404(Deployment, pk=pk)
        tasks.create_repository_metadata.delay(pk)

        return Response(
            {'detail': ugettext('Operation received')},
            status=status.HTTP_200_OK
        )

    @list_route(methods=['get'])
    def generating(self, request, format=None):
        con = get_redis_connection('default')
        result = con.smembers('migasfree:watch:repos')

        serializer = DeploymentSerializer(
            Deployment.objects.filter(pk__in=result),
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

'''
def get_token_for_user(user, scope):
    """
    Generate a new signed token containing
    a specified user limited for a scope (identified as a string).
    """
    data = {"user_%s_id" % scope: user.id}
    return signing.dumps(data)


def get_and_validate_user(username, password):
    """
    Check if user with username/email exists and specified
    password matchs well with existing user password.

    if user is valid,  user is returned else, corresponding
    exception is raised.
    """

    qs = User.objects.filter(Q(username=username) | Q(email=username))
    if len(qs) == 0:
        raise exceptions.APIException(
            _("Username or password does not matches user.")
        )

    user = qs[0]
    if not user.check_password(password):
        raise exceptions.APIException(
            _("Username or password does not matches user.")
        )

    return user


class AuthViewSet(viewsets.ViewSet):
    def create(self, request, **kwargs):
        username = request.DATA.get('username', None)
        password = request.DATA.get('password', None)

        user = get_and_validate_user(username=username, password=password)

        serializer = UserSerializer(user, context={'request': request})
        data = dict(serializer.data)
        data['auth_token'] = get_token_for_user(user, 'authentication')

        return Response(data, status=status.HTTP_200_OK)
'''


class SafePackageViewSet(SafePackagerConnectionMixin, viewsets.ViewSet):
    def create(self, request, format=None):
        """
        claims = {
            'project': project_name,
            'store': store_name,
            'is_package': true|false
        }
        """

        claims = self.get_claims(request.data)
        project = get_object_or_404(Project, name=claims.get('project'))

        store, _ = Store.objects.get_or_create(claims.get('store'), project)

        _file = request.FILES.get('file')

        if claims.get('is_package'):
            package = Package.objects.filter(name=_file.name, project=project)
            if package:
                package[0].update_store(store)
            else:
                Package.objects.create(
                    name=_file.name,
                    project=project,
                    store=store,
                    file_list=[_file]
                )

        target = os.path.join(
            settings.MIGASFREE_PUBLIC_DIR,
            project.slug,
            'stores',
            store.slug,
            _file.name
        )
        Package.handle_uploaded_file(_file, target)

        return Response(
            self.create_response(ugettext('Data received')),
            status=status.HTTP_200_OK
        )

    @list_route(methods=['post'], url_path='set')
    def packageset(self, request, format=None):
        """
        claims = {
            'project': project_name,
            'store': store_name,
            'packageset': string,
            'path': string
        }
        """

        claims = self.get_claims(request.data)
        project = get_object_or_404(Project, name=claims.get('project'))

        store, _ = Store.objects.get_or_create(claims.get('store'), project)

        _file = request.FILES.get('file')

        target = os.path.join(
            settings.MIGASFREE_PUBLIC_DIR,
            project.slug,
            'stores',
            store.slug,
            claims.get('packageset'),
            _file.name
        )

        package = Package.objects.filter(
            name=claims.get('packageset'), project=project
        )
        if package:
            package[0].update_store(store)
        else:
            Package.objects.create(
                name=claims.get('packageset'),
                project=project,
                store=store,
                file_list=[_file]
            )

        Package.handle_uploaded_file(_file, target)

        # if exists path move it
        if claims.get('path'):
            dst = os.path.join(
                settings.MIGASFREE_PUBLIC_DIR,
                project.slug,
                'stores',
                store.slug,
                claims.get('packageset'),
                claims.get('path'),
                _file.name
            )
            try:
                os.makedirs(os.path.dirname(dst))
            except OSError:
                pass
            os.rename(target, dst)

        return Response(
            self.create_response(ugettext('Data received')),
            status=status.HTTP_200_OK
        )

    @list_route(methods=['post'], url_path='repos')
    def create_repository(self, request, format=None):
        """
        claims = {
            'project': project_name,
            'packageset': name,
        }
        """

        claims = self.get_claims(request.data)
        if not claims or 'project' not in claims or 'packageset' not in claims:
            return Response(
                self.create_response(ugettext('Malformed claims')),
                status=status.HTTP_400_BAD_REQUEST
            )

        project = get_object_or_404(Project, name=claims.get('project'))
        package = get_object_or_404(
            Package, name=claims.get('packageset'), project=project
        )

        deployments = Deployment.objects.filter(
            available_packages__id=package.id
        )
        for deploy in deployments:
            tasks.create_repository_metadata.delay(deploy.id)

        return Response(
            self.create_response(ugettext('Data received')),
            status=status.HTTP_200_OK
        )
