from rest_framework import serializers
from rest_polymorphic.serializers import PolymorphicSerializer
from ..models import hooks


class HookServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = hooks.HookServer
        fields = "__all__"


class HttpHookSerializer(serializers.ModelSerializer):
    class Meta:
        model = hooks.HttpHook
        fields = "__all__"


class HookSerializer(PolymorphicSerializer):
    model_serializer_mapping = {
        hooks.HttpHook: HttpHookSerializer,
    }