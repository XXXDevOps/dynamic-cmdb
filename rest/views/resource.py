import uuid
from django.conf import settings
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.filters import OrderingFilter, SearchFilter, BaseFilterBackend
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from ..rest_exceptions import LockedException
from ..serializers import resource as resource_serializer
from ..models import attribute as attribute_model
from ..models import attribute_defined as attribute_defined_model
from ..models import resource as resource_model
from ..models import resource_defined as resource_defined_model
from ..models import service as service_model


class ResourceAttributeSearchBackend(BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        search = request.query_params.get('search', None)
        queryset = queryset.filter(attributes__in=attribute_model.Attribute.objects.filter(value__like=search).all())
        return queryset


class ResourceViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    # filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    # search_fields = ('$id', '$name', '$departments__name', '$labels__k', '$labels__v')
    filterset_fields = ('name',)
    ordering_fields = ('name', '_ctime', '_mtime')

    @staticmethod
    def get_attribute_classname_by_attribute_defined(x):
        return x[:-7]

    # TODO: tunning name represent perform, disable FK serializer use sub query
    def get_m2m_or_fk_attr_query_set_map(self, query):
        if not getattr(self, 'm2m_or_fk_attr_defined_map', False):
            return {}
        r_ls = []
        m2m_query = []
        for x in query:
            for y in x.attributes.all():
                if y.value:
                    if isinstance(y, attribute_model.Many2ManyAttribute):
                        m2m_query = y.value.values()
                    elif isinstance(y, attribute_model.ForeignKeyAttribute):
                        r_ls.append(y.value.pk)

        r = resource_model.Resource.objects.filter(id__in=r_ls)
        fr = {x.id: x.name for x in r}
        if m2m_query:
            for x in m2m_query:
                fr[x['name']] = x['name']
        return fr

    def retrieve(self, request, *args, **kwargs):
        rd = self.get_resource_defined()
        instance = self.get_object()
        relate_resources_map = self.get_m2m_or_fk_attr_query_set_map([instance])
        serializer = self.get_serializer(instance, relate_resources_map=relate_resources_map)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        rd = self.get_resource_defined()
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            relate_resources_map = self.get_m2m_or_fk_attr_query_set_map(page)
            serializer = self.get_serializer(
                page,
                many=True,
                relate_resources_map=relate_resources_map
            )
            return self.get_paginated_response(serializer.data)
        relate_resources_map = self.get_m2m_or_fk_attr_query_set_map(queryset)
        serializer = self.get_serializer(queryset, many=True, relate_resources_map=relate_resources_map)
        return Response(serializer.data)

    def get_resource_defined(self):
        resource_defined = self.kwargs.get('resource_defined')
        resource_id = self.kwargs.get('resource_id')
        m2m_or_fk_attr = self.kwargs.get('m2m_or_fk_attr')
        rd = getattr(self, 'rd', None)

        if rd is None:
            rd = resource_defined_model.ResourceDefined.objects.prefetch_related('attributes').get(name=resource_defined)
            if resource_id and m2m_or_fk_attr:
                attr_defined = rd.attributes.get(name=m2m_or_fk_attr)
                if isinstance(attr_defined, attribute_model.Many2ManyAttributeDefined):
                    second_rd = resource_defined_model.ResourceDefined.objects.prefetch_related('attributes')\
                        .get(pk=attr_defined.relate.pk)
                    setattr(self, 'nest_resource_id', resource_id)
                    setattr(self, 'm2m_attr_defined', attr_defined)
                    rd = second_rd
                elif isinstance(attr_defined, attribute_defined_model.ForeignKeyAttributeDefined):
                    second_rd = resource_defined_model.ResourceDefined.objects.prefetch_related('attributes').get(
                        pk=attr_defined.relate.pk)
                    setattr(self, 'nest_resource_id', resource_id)
                    setattr(self, 'fk_attr_defined', attr_defined)
                    rd = second_rd
            setattr(self, 'rd', rd)
            m2m_or_fk_attr_defined_map = {}
            for x in rd.attributes.all():
                if isinstance(x, attribute_defined_model.Many2ManyAttributeDefined):
                    m2m_or_fk_attr_defined_map[x.name] = {
                        'rd': x.relate, 'attr_class': attribute_model.Many2ManyAttribute}
                elif isinstance(x, attribute_defined_model.ForeignKeyAttributeDefined):
                    m2m_or_fk_attr_defined_map[x.name] = {
                        'rd': x.relate, 'attr_class': attribute_model.ForeignKeyAttribute}
            setattr(self, 'm2m_or_fk_attr_defined_map', m2m_or_fk_attr_defined_map)

        return rd

    def filter_queryset_from_request(self, queryset):
        rd = self.get_resource_defined()
        m = {x.name: x for x in rd.attributes.all()}
        fqs = []
        nfqs = {}
        # name = None
        search = self.request.query_params.get('search')
        for k, v in self.request.query_params.items():
            # 过滤空参数
            if v == '':
                continue
            if k.startswith('~'):
                k2 = k[1:]
                pattern = "%s___value__iregex"
            elif k.startswith('!'):
                k2 = k[1:]
                pattern = "%s___value__ne"
            elif k.endswith('__gte'):
                k2 = k[:-5]
                pattern = "%s___value__gte"
            elif k.endswith('__gt'):
                k2 = k[:-4]
                pattern = "%s___value__gt"
            elif k.endswith('__lte'):
                k2 = k[:-5]
                pattern = "%s___value__lte"
            elif k.endswith('__lt'):
                k2 = k[:-4]
                pattern = "%s___value__lt"
            else:
                k2 = k
                pattern = "%s___value"
            if k2 in m:
                if isinstance(m[k2], attribute_defined_model.ForeignKeyAttributeDefined):
                    pattern = pattern.replace("value", "value__name")
                acn = self.get_attribute_classname_by_attribute_defined(m[k2].__class__.__name__)
                q_kwargs = {pattern % acn: v}
                tmp_fq = Q(attributeDefined=m[k2]) & Q(**q_kwargs)
                fqs.append(tmp_fq)
            elif k2 in ['_ctime', '_mtime', 'name']:
                pattern = pattern.replace("___value", "")
                nfqs[pattern % k2] = v
        if search:
            search_fq = None
            for k, v in m.items():
                if v.__class__ not in [attribute_defined_model.PKStringAttributeDefined,
                                       attribute_defined_model.StringAttributeDefined,
                                       attribute_defined_model.TextAttributeDefined]:
                    continue
                acn = self.get_attribute_classname_by_attribute_defined(v.__class__.__name__)
                q_kwargs = {"%s___value__icontains" % acn: search}
                if not search_fq:
                    search_fq = Q(attributeDefined=v) & Q(**q_kwargs)
                else:
                    search_fq = search_fq | (Q(attributeDefined=v) & Q(**q_kwargs))
            queryset = queryset.filter(
                Q(attributes__in=attribute_model.Attribute.objects.filter(search_fq).all()) | Q(name__icontains=search)
            )
        for fq in fqs:
            queryset = queryset.filter(attributes__in=attribute_model.Attribute.objects.filter(fq).all())
        if nfqs:
            queryset = queryset.filter(**nfqs)
        return queryset

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
            uuid.UUID(value)
            filter_kwargs = {self.lookup_field: value}
        except (AttributeError, ValueError):
            filter_kwargs = {'name': value}

        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def get_queryset(self):
        try:
            rd = self.get_resource_defined()
            m2m_attr_defined = getattr(self, 'm2m_attr_defined', None)
            fk_attr_defined = getattr(self, 'fk_attr_defined', None)
            resource_id = getattr(self, 'nest_resource_id', None)
            if resource_id is not None and m2m_attr_defined is not None:
                queryset_condition = resource_model.Resource.objects.get(pk=resource_id)\
                    .attributes.filter(attributeDefined=m2m_attr_defined)
                queryset = resource_model.Resource.objects.filter(many2manyattribute__in=queryset_condition).filter(type=rd) \
                    .prefetch_related('departments', 'labels', 'attributes').distinct()
            elif resource_id is not None and fk_attr_defined is not None:
                queryset_condition = resource_model.Resource.objects.get(name=resource_id)\
                    .attributes.filter(attributeDefined=fk_attr_defined)
                queryset = resource_model.Resource.objects.filter(foreignkeyattribute__in=queryset_condition).filter(type=rd) \
                    .prefetch_related('departments', 'labels', 'attributes').distinct()
            else:
                queryset = resource_model.Resource.objects.filter(type=rd)\
                    .prefetch_related('departments', 'labels', 'attributes').distinct()
            queryset = self.filter_queryset_from_request(queryset)
        except Exception as e:
            raise NotFound('not found resource: %r' % e)
        return queryset

    def get_serializer_class(self):
        # compatibilized the rest-framework docs api
        if self.request is None:
            return resource_serializer.ResourceSerializer
        sc = getattr(self, 'my_sc', None)
        if sc is None:
            select_fields = self.get_fields_filter_from_request()
            setattr(self, 'select_fields', select_fields)
            rd = self.get_resource_defined()
            attr_map = {
                x.name: (
                    x.id,
                    ResourceViewSet.get_attribute_classname_by_attribute_defined(x.__class__.__name__),
                    x
                ) for x in rd.attributes.all()
            }
            de_attr_map = {x.id: x for x in rd.attributes.all()}

            def tmp_serializer(*args, **kwargs):
                kwargs['attr_map'] = attr_map
                kwargs['de_attr_map'] = de_attr_map
                kwargs['resourceDefined'] = rd
                kwargs['select_fields'] = select_fields
                return resource_serializer.ResourceSerializer(*args, **kwargs)

            setattr(self, 'my_sc', tmp_serializer)
            return tmp_serializer
        else:
            return sc

    def get_fields_filter_from_request(self):
        select_fields = self.request.query_params.get('fields', None)
        if select_fields:
            select_fields = select_fields.split(',')
        else:
            select_fields = None
        return select_fields

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            if settings.RESOURCE_MODIFY_LOCK and instance.is_locked:
                raise LockedException()
            for x in instance.attributes.all():
                x.delete()
            instance.delete()
            # delete hook
            if instance.type.create_hook is not None:
                instance.type.create_hook.trigger(self.get_serializer_class().to_representation(instance))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def env(self, request, resource_defined,  pk=None):
        service_id = request.query_params.get('service_id', None)
        try:
            r = self.get_object()
        except resource_model.Resource.DoesNotExist:
            return Response(status=404, data={'code': 404, 'detail': 'no such resource'})
        else:
            se = {}
            if service_id:
                try:
                    s = r.service_set.get(id=int(service_id))
                except service_model.Service.DoesNotExist:
                    return Response(status=404, data={'code': 404, 'detail': 'no such service, or resource not bind this service'})
                else:
                    se = s.get_env(include_self=True)
            try:
                reo = resource_model.ResourceEnv.objects.get(resource=r)
            except resource_model.ResourceEnv.DoesNotExist:
                re = {}
            else:
                re = {k: {'value': v, 'inherit': False, 'path': None, 'service_id': None} for k, v in reo.env.items()}
            se.update(re)
            return Response(se)

    @action(detail=True, methods=['post'])
    def set_env(self, request, resource_defined, pk=None):
        env_json = request.data
        try:
            r = self.get_object()
        except resource_model.Resource.DoesNotExist:
            return Response(status=404, data={'code': 404, 'detail': 'no such resource'})
        else:
            env, _ = resource_model.ResourceEnv.objects.get_or_create(resource=r)
            env.env = env_json
            env.save()
            return Response(env_json)

    @action(detail=True, methods=['get'])
    def lock(self, request, resource_defined, pk=None):
        if not settings.RESOURCE_MODIFY_LOCK:
            raise NotFound
        rd = self.get_resource_defined()
        system = request.query_params.get('system')
        try:
            expire = int(request.query_params.get('expire', 60))
            exclusive = int(request.query_params.get('exclusive', 0))
        except ValueError:
            expire = 60
            exclusive = 0
        try:
            r = resource_model.Resource.objects.get(type=rd, pk=pk)
        except attribute_defined_model.AttributeDefined.DoesNotExist:
            return Response(status=404, data={'code': 404, 'detail': 'no such resource'})
        else:
            r.lock(system=system, expire=expire, exclusive=True if exclusive == 1 else False)
        return Response({'success': True})

    @action(detail=True, methods=['get'])
    def unlock(self, request, resource_defined, pk=None):
        if not settings.RESOURCE_MODIFY_LOCK:
            raise NotFound
        rd = self.get_resource_defined()
        try:
            r = resource_model.Resource.objects.get(type=rd, pk=pk)
        except attribute_defined_model.AttributeDefined.DoesNotExist:
            return Response(status=404, data={'code': 404, 'detail': 'no such resource'})
        else:
            system = request.query_params.get('system')
            r.unlock(system=system)
        return Response({'success': True})

    @action(detail=True, methods=['get'])
    def get_locks(self, request, resource_defined, pk=None):
        if not settings.RESOURCE_MODIFY_LOCK:
            raise NotFound
        rd = self.get_resource_defined()
        try:
            r = resource_model.Resource.objects.get(type=rd, pk=pk)
        except attribute_defined_model.AttributeDefined.DoesNotExist:
            return Response(status=404, data={'code': 404, 'detail': 'no such resource'})
        else:
            system = request.query_params.get('system')
            return Response(r.get_locks(system=system))

    @action(detail=False, methods=['get'])
    def distinct(self, request, resource_defined):
        column = request.query_params.get('column')
        rd = self.get_resource_defined()
        queryset = self.filter_queryset_from_request(self.get_queryset())
        try:
            atd = rd.attributes.get(name=column)
        except attribute_defined_model.AttributeDefined.DoesNotExist:
            return Response(status=404, data={'code': 404, 'detail': 'no such column'})
        r = set(
            [x.value
             for x in attribute_model.Attribute.objects.filter(attributeDefined=atd, resource__in=queryset)
             if hasattr(x, 'value')]
        )
        return Response(r)

    @action(detail=False, methods=['get'])
    def groupby(self, request, resource_defined):
        column = request.query_params.get('column')
        rd = self.get_resource_defined()
        queryset = self.filter_queryset_from_request(self.get_queryset())
        try:
            atd = rd.attributes.get(name=column)
        except attribute_defined_model.AttributeDefined.DoesNotExist:
            return Response(status=404, data={'code': '404', 'detail': 'no such column'})
        r = [x.value
             for x in attribute_model.Attribute.objects.filter(attributeDefined=atd, resource__in=queryset)
             if hasattr(x, 'value')]
        r_m = {}
        for x in r:
            if x in r_m:
                r_m[x] += 1
            else:
                r_m[x] = 1
        return Response(r_m)

    @action(detail=False, methods=['get'])
    def count(self, request, resource_defined):
        rd = self.get_resource_defined()
        queryset = self.filter_queryset_from_request(self.get_queryset())
        c = queryset.all().count()
        return Response({'count': c, 'resource-defined': rd.name})


class BackupResourceViewSet(viewsets.ModelViewSet):
    serializer_class = resource_serializer.BackupResourceSerializer
    queryset = resource_model.BackupResource.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['resource_id', 'version']
    ordering_fields = ('_ctime', '_mtime')


class LabelKeyViewSet(viewsets.ViewSet):
    def list(self, request):
        values = resource_model.Label.objects.values('k').distinct()
        return Response([x['k'] for x in values])


class LabelValueViewSet(viewsets.ViewSet):
    def list(self, request, label_k):
        values = resource_model.Label.objects.filter(k=label_k).values('v').distinct()
        return Response([x['v'] for x in values])