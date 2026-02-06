# Copyright (c) 2015-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2026 Alberto Gacías <alberto@migasfree.org>
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

from django.contrib.auth.models import Group, Permission
from django.db.models import Prefetch
from django.utils.translation import gettext
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ....mixins import DatabaseCheckMixin
from ...filters import (
    DomainFilter,
    GroupFilter,
    PermissionFilter,
    ScopeFilter,
    UserProfileFilter,
)
from ...models import Attribute, Domain, Scope, UserProfile
from ...serializers import (
    ChangePasswordSerializer,
    DomainListSerializer,
    DomainSerializer,
    DomainWriteSerializer,
    GroupSerializer,
    GroupWriteSerializer,
    PermissionSerializer,
    ScopeListSerializer,
    ScopeSerializer,
    ScopeWriteSerializer,
    UserProfileListSerializer,
    UserProfileSerializer,
    UserProfileWriteSerializer,
)
from .base import ExportViewSet, MigasViewSet


@extend_schema(tags=['user-profiles'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: username, first_name, last_name',
            type=str,
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class UserProfileViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = UserProfile.objects.select_related(
        'user',
        'domain_preference',
    ).prefetch_related(
        'domains',
        'groups',
        'user_permissions',
    )
    serializer_class = UserProfileSerializer
    filterset_class = UserProfileFilter
    search_fields = ('username', 'first_name', 'last_name')
    ordering_fields = '__all__'
    ordering = ('username',)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return UserProfileWriteSerializer

        if self.action == 'list':
            return UserProfileListSerializer

        return UserProfileSerializer

    def get_queryset(self):
        if self.request is None:
            return UserProfile.objects.none()

        return self.queryset.select_related('domain_preference', 'scope_preference').prefetch_related(
            'domains',
            'groups',
            'user_permissions',
        )

    @action(methods=['get'], detail=False, url_path='domain-admins')
    def domain_admins(self, request):
        serializer = UserProfileSerializer(
            UserProfile.objects.filter(groups__in=[Group.objects.get(name='Domain Admin')]).order_by('username'),
            many=True,
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path='update-token')
    def set_token(self, request, pk=None):
        user = self.get_object()
        token = user.update_token()

        return Response(
            {'detail': gettext('Token updated!'), 'info': token},
            status=status.HTTP_200_OK,
        )

    @action(
        methods=['put'],
        detail=True,
        serializer_class=ChangePasswordSerializer,
        url_path='change-password',
    )
    def set_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            user.update_password(serializer.validated_data.get('password'))

            return Response({'detail': gettext('Password changed!')}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['accounts'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: name',
            type=str,
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class GroupViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, ExportViewSet):
    queryset = Group.objects.prefetch_related(
        'user_set',
        'permissions',
    )
    serializer_class = GroupSerializer
    filterset_class = GroupFilter
    search_fields = ('name',)
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return GroupWriteSerializer

        return GroupSerializer


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: name',
            type=str,
        )
    ],
    methods=['GET'],
    tags=['accounts'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class PermissionViewSet(DatabaseCheckMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    filterset_class = PermissionFilter
    search_fields = ('name',)


@extend_schema(tags=['domains'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: name',
            type=str,
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class DomainViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = Domain.objects.prefetch_related(
        'included_attributes',
        'included_attributes__property_att',
        'excluded_attributes',
        'excluded_attributes__property_att',
        'userprofile_set',
    )
    serializer_class = DomainSerializer
    filterset_class = DomainFilter
    search_fields = ('name',)
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return DomainWriteSerializer

        if self.action == 'list':
            return DomainListSerializer

        return DomainSerializer

    def get_queryset(self):
        if self.request is None:
            return Domain.objects.none()

        if self.action == 'list':
            return self.queryset

        return self.queryset.prefetch_related(
            'included_attributes',
            'included_attributes__property_att',
            'excluded_attributes',
            'excluded_attributes__property_att',
            'tags',
        )


@extend_schema(tags=['scopes'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: name',
            type=str,
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class ScopeViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = Scope.objects.prefetch_related(
        'included_attributes',
        'included_attributes__property_att',
        'excluded_attributes',
        'excluded_attributes__property_att',
    )
    serializer_class = ScopeSerializer
    filterset_class = ScopeFilter
    search_fields = ('name',)
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return ScopeWriteSerializer

        if self.action == 'list':
            return ScopeListSerializer

        return ScopeSerializer

    def get_queryset(self):
        if self.request is None:
            return Scope.objects.none()

        filter_by_user = True
        if self.action == 'list':
            filter_by_user = not (self.request.user.userprofile.is_superuser and self.request.GET.get('page', 0))
        else:
            filter_by_user = not self.request.user.userprofile.is_superuser

        qs = Scope.objects.scope(self.request.user.userprofile, filter_by_user)
        if self.action == 'list':
            return qs

        qs_att = Attribute.objects.scope(self.request.user.userprofile)

        return qs.prefetch_related(
            Prefetch('included_attributes', queryset=qs_att),
            'included_attributes__property_att',
            Prefetch('excluded_attributes', queryset=qs_att),
            'excluded_attributes__property_att',
        )
