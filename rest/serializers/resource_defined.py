from rest_framework import serializers
from django.db import transaction
from ..models import attribute_defined
from .attribute_defined import AttributeDefinedSerializer


class ResourceDefinedSerializer(serializers.ModelSerializer):
    attributes = AttributeDefinedSerializer(many=True, required=True)

    def create(self, validated_data):
        attributes = validated_data.pop('attributes', [])
        with transaction.atomic():
            r = self.Meta.model.objects.create(**validated_data)
            for attribute in attributes:
                resourcetype = attribute.pop('resourcetype')
                attribute['resourceDefined'] = r
                getattr(attribute_defined, resourcetype).objects.create(**attribute)
        return r

    def update(self, instance, validated_data):
        # attributes = validated_data.pop('attributes', [])
        instance.name = validated_data['name']
        instance.create_hook = validated_data['create_hook']
        instance.update_hook = validated_data['update_hook']
        instance.delete_hook = validated_data['delete_hook']
        instance.enable_version_check = validated_data['enable_version_check']
        instance.enable_rollback = validated_data['enable_rollback']
        instance.save()
        return instance
    # 这里缺个update nest 方法
    class Meta:
        model = attribute_defined.ResourceDefined
        fields = "__all__"