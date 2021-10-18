from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter, BaseFilterBackend
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from ..serializers import resource_defined as resource_defined_serializer
from ..models import resource as resource_model


class ResourceDefinedIdsFilterBackend(BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        ids = request.query_params.getlist('[]ids', None)
        if ids:
            queryset = queryset.filter(pk__in=ids)
        return queryset


class ResourceDefinedViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = resource_model.ResourceDefined.objects.all()
    serializer_class = resource_defined_serializer.ResourceDefinedSerializer
    filter_backends = [ResourceDefinedIdsFilterBackend,  SearchFilter, OrderingFilter]
    search_fields = ('$name', )
    ordering_fields = ('name', '_ctime', '_mtime')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        with transaction.atomic():
            for x in instance.attributes.all():
                x.delete()
            self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        assert lookup_url_kwarg in self.kwargs, (
                'Expected view %s to be called with a URL keyword argument '
                'named "%s". Fix your URL conf, or set the `.lookup_field` '
                'attribute on the view correctly.' %
                (self.__class__.__name__, lookup_url_kwarg)
        )
        # 重写源码get_object操作
        # filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        value = self.kwargs[lookup_url_kwarg]
        try:
            int(value)
            filter_kwargs = {self.lookup_field: value}
        except (AttributeError, ValueError):
            filter_kwargs = {'name': value}

        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj