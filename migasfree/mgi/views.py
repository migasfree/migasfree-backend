import requests
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from migasfree.mgi.models import Build, Config, Flavour, Release
from migasfree.mgi.serializers import BuildSerializer, ConfigSerializer, FlavourSerializer, ReleaseSerializer


@extend_schema(tags=['mgi'])
class ConfigViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Config.objects.all()
    serializer_class = ConfigSerializer


@extend_schema(tags=['mgi'])
class FlavourViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Flavour.objects.all()
    serializer_class = FlavourSerializer
    filterset_fields = ('config', 'enabled', 'name')
    search_fields = ('name', 'description')


@extend_schema(tags=['mgi'])
class ReleaseViewSet(viewsets.ModelViewSet):
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
class BuildViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Build.objects.all()
    serializer_class = BuildSerializer
    filterset_fields = ('release', 'flavour', 'status')
