from rest_framework import serializers

from ..core.models import ServerAttribute
from ..core.serializers import ProjectInfoSerializer
from .models import Build, Config, Flavour, Release


class ConfigSerializer(serializers.ModelSerializer):
    dockerfile = serializers.CharField(required=False, allow_blank=True)
    project = ProjectInfoSerializer(many=False, read_only=True)

    class Meta:
        model = Config
        fields = (
            'id',
            'project',
            'template_id',
            'build_type',
            'base_os',
            'partition',
            'provision_script',
            'image_format',
            'config',
            'dockerfile',
        )
        read_only_fields = ('id',)


class FlavourSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=ServerAttribute.objects.filter(property_att__sort='server'), required=False
    )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = ', '.join(str(tag) for tag in instance.tags.all())
        return representation

    class Meta:
        model = Flavour
        fields = '__all__'


class ReleaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Release
        fields = '__all__'
        read_only_fields = ('created_at',)


class BuildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Build
        fields = '__all__'
