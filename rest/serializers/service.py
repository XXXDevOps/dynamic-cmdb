from rest_framework import serializers
from django.db import transaction
from ..models.service import Service
from ..models import resource as resource_model
from .resource import SimpleResourceSerializer


class ServiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Service
        fields = ('id', 'name', 'level', 'parent', 'children', 'tree_path_cache')


class ServiceDetailSerializer(serializers.ModelSerializer):
    resources = SimpleResourceSerializer(many=True)

    def update(self, instance, validated_data):
        with transaction.atomic():
            rename = False
            resources = validated_data.pop('resources', None)
            validated_data.pop('children', None)
            if resources is not None:
                resource_objs = resource_model.Resource.objects.filter(id__in=[x['id'] for x in resources])
                instance.resources.set(resource_objs)
            if validated_data['name'] != instance.name:
                rename = True
            for k,v in validated_data.items():
                setattr(instance, k, v)
            instance.save()
            if rename:
                instance.refresh_child_cache()
        return instance

    def create(self, validated_data):
        with transaction.atomic():
            resources = validated_data.pop('resources', None)
            validated_data.pop('children', None)
            instance = Service.objects.create(**validated_data)
            if resources is not None:
                resource_objs = resource_model.Resource.objects.filter(id__in=[x['id'] for x in resources])
                instance.resources.set(resource_objs)
            for k,v in validated_data.items():
                setattr(instance, k, v)
            instance.save()
        return instance

    class Meta:
        model = Service
        fields = ('id', 'name', 'level', 'parent', 'resources', 'env', 'tree_path_cache')


class ServiceTreeSerializer(serializers.ModelSerializer):
    childs = serializers.SerializerMethodField('get_children')

    class Meta:
        model = Service
        fields = ('id', 'name', 'level', 'parent', 'childs', 'tree_path_cache')

    def get_children(self, obj):
        children = []
        for x in obj.get_children():
            serializer = self.__class__(x, context=self.context)
            children.append(serializer.data)
        return children