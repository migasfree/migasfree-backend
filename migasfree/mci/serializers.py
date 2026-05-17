from rest_framework import serializers

from migasfree.core.models import ServerAttribute
from migasfree.mci.models import Build, Config, Flavour, Release


class ConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = Config
        fields = ('id', 'project', 'template_id', 'base_os', 'dockerfile', 'partition')
        read_only_fields = ('id', 'base_os', 'dockerfile', 'partition')


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
