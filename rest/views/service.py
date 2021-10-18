from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter, BaseFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from mptt.templatetags.mptt_tags import cache_tree_children
from ..serializers import service as service_serializer
from ..models import service as service_model


class TreeFilterBackend(BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        queryset = service_model.Service.objects.get_queryset_descendants(queryset, include_self=True)
        queryset = service_model.Service.objects.get_queryset_ancestors(queryset, include_self=True)
        queryset = cache_tree_children(queryset)
        return queryset


class ServiceViewSet(viewsets.ModelViewSet):
    serializer_class = service_serializer.ServiceDetailSerializer
    queryset = service_model.Service.objects
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['level', 'name', 'parent']
    search_fields = ('$id', '$name')
    ordering_fields = ('name', '_ctime', '_mtime')

    @action(detail=True, methods=['get'])
    def env(self, request, pk=None):
        s = self.get_object()
        return Response(s.get_env())


class ServiceTreeViewSet(viewsets.ModelViewSet):
    serializer_class = service_serializer.ServiceTreeSerializer
    queryset = service_model.Service.objects.select_related('parent')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter, TreeFilterBackend]
    filterset_fields = ['level', 'name', 'id']
    search_fields = ('$id', '$name')
    ordering_fields = ('name', '_ctime', '_mtime')