# -*- coding: utf-8 *-*

# Copyright (c) 2015 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015 Alberto Gacías <alberto@migasfree.org>
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

from django.apps import apps
from django.db.models import Q
from django.shortcuts import render
from django.core import signing
from django.utils.translation import ugettext_lazy as _
# from django.contrib.auth.models import User, Group
from rest_framework import (
    viewsets, parsers, status, mixins,
    exceptions, filters
)
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework_filters import backends

from .models import (
    Platform, Project, Store,
    ServerProperty, ClientProperty,
    ServerAttribute, ClientAttribute,
    Schedule,
    Package, Repository,
)
from .serializers import (
    #UserSerializer, GroupSerializer,
    PlatformSerializer, ProjectSerializer, StoreSerializer,
    ServerPropertySerializer, ClientPropertySerializer,
    ServerAttributeSerializer, ClientAttributeSerializer,
    ScheduleSerializer,
    PackageSerializer, RepositorySerializer,
)
from .filters import RepositoryFilter, PackageFilter
from .permissions import PublicPermission, IsAdminOrIsSelf


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
    permission_classes = (PublicPermission,)


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer


class ServerPropertyViewSet(viewsets.ModelViewSet):
    queryset = ServerProperty.objects.filter(sort='server')
    serializer_class = ServerPropertySerializer


class ClientPropertyViewSet(viewsets.ModelViewSet):
    queryset = ClientProperty.objects.filter(sort='client')
    serializer_class = ClientPropertySerializer


class ServerAttributeViewSet(viewsets.ModelViewSet):
    queryset = ServerAttribute.objects.filter(property_att__sort='server')
    serializer_class = ServerAttributeSerializer


class ClientAttributeViewSet(viewsets.ModelViewSet):
    queryset = ClientAttribute.objects.filter(property_att__sort='client')
    serializer_class = ClientAttributeSerializer


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer


class PackageViewSet(mixins.CreateModelMixin,
        mixins.RetrieveModelMixin,
        mixins.DestroyModelMixin,
        mixins.ListModelMixin,
        viewsets.GenericViewSet):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    filter_class = PackageFilter
    parser_classes = (parsers.MultiPartParser, parsers.FormParser,)


class RepositoryViewSet(viewsets.ModelViewSet):
    queryset = Repository.objects.all()
    serializer_class = RepositorySerializer
    filter_class = RepositoryFilter
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend)
    ordering_fields = '__all__'
    ordering = ('-start_date',)

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
