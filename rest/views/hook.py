from rest_framework import viewsets
from ..serializers import hooks as hook_serializer
from ..models import hooks as hook_model


class HookViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    serializer_class = hook_serializer.HookSerializer
    queryset = hook_model.BaseHook.objects.all()


class HookServerViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    serializer_class = hook_serializer.HookServerSerializer
    queryset = hook_model.HookServer.objects.all()
