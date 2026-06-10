import requests
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..core.views import MigasViewSet
from .models import Build, Config, Flavour, Release
from .serializers import BuildSerializer, ConfigSerializer, FlavourSerializer, ReleaseSerializer


@extend_schema(tags=['mgi'])
class ConfigViewSet(viewsets.ModelViewSet, MigasViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Config.objects.all()
    serializer_class = ConfigSerializer


@extend_schema(tags=['mgi'])
class FlavourViewSet(viewsets.ModelViewSet, MigasViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Flavour.objects.all()
    serializer_class = FlavourSerializer
    filterset_fields = ('config', 'enabled', 'name')
    search_fields = ('name', 'description')


@extend_schema(tags=['mgi'])
class ReleaseViewSet(viewsets.ModelViewSet, MigasViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Release.objects.all()
    serializer_class = ReleaseSerializer
    filterset_fields = ('config', 'name')
    search_fields = ('name', 'description')

    @action(detail=True, methods=['post'], url_path='build')
    def build(self, request, pk=None):
        """Trigger an MGI golden image build for this release through the manager."""
        release = self.get_object()

        headers = {}
        if request.auth:
            headers['Authorization'] = f'Bearer {request.auth}'

        try:
            base_url = settings.MIGASFREE_MANAGER_URL
            url = f'{base_url.rstrip("/")}/manager/v1/internal/mgi/build'
            response = requests.post(url, json={'release_id': release.id}, headers=headers, timeout=15.0)

            if response.ok:
                return Response(response.json(), status=status.HTTP_202_ACCEPTED)
            else:
                return Response(
                    {'error': f'Manager responded with HTTP {response.status_code}', 'details': response.text},
                    status=response.status_code,
                )
        except Exception as e:
            return Response(
                {'error': f'Could not connect to manager: {e!s}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(tags=['mgi'])
class BuildViewSet(viewsets.ModelViewSet, MigasViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Build.objects.all()
    serializer_class = BuildSerializer
    filterset_fields = ('release', 'flavour', 'status')

    @action(detail=True, methods=['get'], url_path='status')
    def status(self, request, pk=None):
        """Get the real-time build task status from the manager."""
        build = self.get_object()

        if not build.task_id:
            return Response(
                {'error': 'Build record has no associated task_id'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        try:
            base_url = settings.MIGASFREE_MANAGER_URL
            url = f'{base_url.rstrip("/")}/manager/v1/internal/mgi/build/{build.task_id}/status'
            response = requests.get(url, timeout=15.0)

            if response.ok:
                return Response(response.json(), status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': f'Manager responded with HTTP {response.status_code}', 'details': response.text},
                    status=response.status_code,
                )
        except Exception as e:
            return Response(
                {'error': f'Could not connect to manager: {e!s}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='promote')
    def promote(self, request, pk=None):
        """Promote an MGI build image, enabling it in the catalog."""
        build = self.get_object()

        try:
            base_url = settings.MIGASFREE_MANAGER_URL
            url = f'{base_url.rstrip("/")}/manager/v1/internal/mgi/builds/{build.id}/promote'
            headers = {}
            if request.auth:
                headers['Authorization'] = f'Bearer {request.auth}'
            response = requests.post(url, headers=headers, timeout=15.0)

            if response.ok:
                return Response(response.json(), status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': f'Manager responded with HTTP {response.status_code}', 'details': response.text},
                    status=response.status_code,
                )
        except Exception as e:
            return Response(
                {'error': f'Could not connect to manager: {e!s}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='demote')
    def demote(self, request, pk=None):
        """Demote an MGI build image, disabling it in the catalog."""
        build = self.get_object()

        try:
            base_url = settings.MIGASFREE_MANAGER_URL
            url = f'{base_url.rstrip("/")}/manager/v1/internal/mgi/builds/{build.id}/demote'
            headers = {}
            if request.auth:
                headers['Authorization'] = f'Bearer {request.auth}'
            response = requests.post(url, headers=headers, timeout=15.0)

            if response.ok:
                return Response(response.json(), status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': f'Manager responded with HTTP {response.status_code}', 'details': response.text},
                    status=response.status_code,
                )
        except Exception as e:
            return Response(
                {'error': f'Could not connect to manager: {e!s}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
