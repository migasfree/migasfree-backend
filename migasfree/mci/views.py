import requests
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from migasfree.mci.models import Build, Config, Flavour, Release
from migasfree.mci.serializers import BuildSerializer, ConfigSerializer, FlavourSerializer, ReleaseSerializer


@extend_schema(tags=['mci'])
class ConfigViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Config.objects.all()
    serializer_class = ConfigSerializer


@extend_schema(tags=['mci'])
class FlavourViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Flavour.objects.all()
    serializer_class = FlavourSerializer
    filterset_fields = ('config', 'enabled', 'name')
    search_fields = ('name', 'description')


@extend_schema(tags=['mci'])
class ReleaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Release.objects.all()
    serializer_class = ReleaseSerializer
    filterset_fields = ('config', 'name')
    search_fields = ('name', 'description')

    @action(detail=True, methods=['post'], url_path='build')
    def build(self, request, pk=None):
        """Trigger an MCI golden image build for this release through the manager."""
        release = self.get_object()

        headers = {}
        if request.auth:
            headers['Authorization'] = f'Bearer {request.auth}'

        try:
            manager_url = 'http://manager:8080/manager/v1/internal/mci/build'
            response = requests.post(manager_url, json={'release_id': release.id}, headers=headers, timeout=15.0)

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


@extend_schema(tags=['mci'])
class BuildViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Build.objects.all()
    serializer_class = BuildSerializer
    filterset_fields = ('release', 'flavour', 'status')
