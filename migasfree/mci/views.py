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

    def _fetch_template(self, template_id, auth_token=None):
        headers = {}
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'

        try:
            # Connect to the internal manager service
            manager_url = f'http://manager:8080/manager/v1/internal/mci/templates/{template_id}'
            response = requests.get(manager_url, headers=headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            from rest_framework.exceptions import ValidationError

            raise ValidationError(f'Failed to fetch template {template_id} from manager: {e!s}') from e

    def perform_create(self, serializer):
        template_id = self.request.data.get('template_id')
        if template_id:
            template_data = self._fetch_template(template_id, self.request.auth)
            serializer.save(
                base_os=template_data.get('base_os', ''),
                dockerfile=template_data.get('dockerfile', ''),
                partition=template_data.get('partition', ''),
            )
        else:
            serializer.save()

    @action(detail=True, methods=['post'])
    def import_template(self, request, pk=None):
        config = self.get_object()
        template_id = request.data.get('template_id')

        if not template_id:
            return Response({'error': 'template_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        template_data = self._fetch_template(template_id, request.auth)

        config.template_id = template_id
        config.base_os = template_data.get('base_os', '')
        config.dockerfile = template_data.get('dockerfile', '')
        config.partition = template_data.get('partition', '')
        config.save()

        serializer = self.get_serializer(config)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def initialize(self, request):
        # We accept both 'project' and 'project_id'
        project_id = request.data.get('project') or request.data.get('project_id')
        template_id = request.data.get('template_id')

        if not project_id or not template_id:
            return Response({'error': 'project_id and template_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Get template data
        template_data = self._fetch_template(template_id, request.auth)

        # Create or update Config
        config, created = Config.objects.update_or_create(
            project_id=project_id,
            defaults={
                'template_id': template_id,
                'base_os': template_data.get('base_os', ''),
                'dockerfile': template_data.get('dockerfile', ''),
                'partition': template_data.get('partition', ''),
            },
        )

        # Create default Flavour
        _, f_created = Flavour.objects.get_or_create(
            config=config,
            name='Default',
            defaults={
                'user': 'migasfree',
                'password': 'migasfree-password',
                'hostname': config.project.name.lower().replace(' ', '-'),
            },
        )

        return Response(
            {'config': self.get_serializer(config).data, 'config_created': created, 'flavour_created': f_created},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


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


@extend_schema(tags=['mci'])
class BuildViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Build.objects.all()
    serializer_class = BuildSerializer
    filterset_fields = ('release', 'flavour', 'status')
