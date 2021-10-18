from uuid import UUID
from rest_framework import serializers
from rest_framework.fields import SkipField
from rest_framework.settings import api_settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.conf import settings
from collections.abc import Mapping
from rest_framework.fields import get_error_detail, set_value
from rest_framework.exceptions import APIException
from rest_framework.relations import PKOnlyObject
from rest_framework.exceptions import ValidationError
from django.db import transaction
from ..protect_keyword import PROTECT_ATTRIBUTES
from collections import OrderedDict
from ..models import resource, attribute, attribute_defined, resource_defined
from ..rest_exceptions import ContentChangedException, LockedException
from .attribute import AttributeSerializer


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = resource.Label
        fields = ('k', 'v')


class ResourceSerializer(serializers.ModelSerializer):
    attributes = AttributeSerializer(many=True, required=False)
    labels = LabelSerializer(many=True, required=False)

    def __init__(self, *args, **kwargs):
        self.attr_map = kwargs.pop('attr_map', {})
        self.de_attr_map = kwargs.pop('de_attr_map', {})
        self.select_fields = kwargs.pop('select_fields', None)
        self.resourceDefined = kwargs.pop('resourceDefined', None)
        self.relate_resources_map = kwargs.pop('relate_resources_map', {})

        super(ResourceSerializer, self).__init__(*args, **kwargs)
    # def __init__(self, instance=None, data=empty, **kwargs):
    #     self.instance = instance
    #     if data is not empty:
    #         self.initial_data = data
    #     self.partial = kwargs.pop('partial', False)
    #     self._context = kwargs.pop('context', {})
    #     kwargs.pop('many', None)
    #     self.attr_map = kwargs.pop('attr_map', {})
    #     self.de_attr_map = kwargs.pop('de_attr_map', {})
    #     self.resourceDefined = kwargs.pop('resourceDefined', None)
    #     super().__init__(**kwargs)

    def to_internal_value(self, data):
        """
                Dict of native values <- Dict of primitive datatypes.
                """
        if not isinstance(data, Mapping):
            message = self.error_messages['invalid'].format(
                datatype=type(data).__name__
            )
            raise ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: [message]
            }, code='invalid')

        data['attributes'] = []
        # resource_id = data['id']
        ret = OrderedDict()
        ret['type'] = self.resourceDefined
        errors = OrderedDict()
        fields = self._writable_fields

        for k, v in self.attr_map.items():
            data['attributes'].append(
                {
                    'value': data.get(k, None),
                    'attributeDefined': v[0],
                    'resourcetype': v[1]
                }
            )
        for field in fields:
            validate_method = getattr(self, 'validate_' + field.field_name, None)
            primitive_value = field.get_value(data)
            try:
                validated_value = field.run_validation(primitive_value)
                if validate_method is not None:
                    validated_value = validate_method(validated_value)
            except ValidationError as exc:
                errors[field.field_name] = exc.detail
            except DjangoValidationError as exc:
                errors[field.field_name] = get_error_detail(exc)
            except SkipField:
                pass
            else:
                set_value(ret, field.source_attrs, validated_value)
        if errors:
            raise ValidationError(errors)
        return ret

    def to_representation(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        ret = OrderedDict()
        fields = self._readable_fields
        for field in fields:
            # dynamic filter fields
            if self.select_fields is not None and field.field_name != PROTECT_ATTRIBUTES and field.field_name not in self.select_fields:
                continue
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue

            # We skip `to_representation` for `None` values so that fields do
            # not have to explicitly deal with that case.
            #
            # For related fields with `use_pk_only_optimization` we need to
            # resolve the pk value.
            check_for_none = attribute.pk if isinstance(attribute, PKOnlyObject) else attribute
            if check_for_none is None:
                ret[field.field_name] = None
            else:
                ret[field.field_name] = field.to_representation(attribute)

        attributes = ret.pop(PROTECT_ATTRIBUTES)
        for k, v in self.de_attr_map.items():
            # 等attributeDefined增加时可以同时增加资源的attribute属性的时候 可以增加默认值功能,否则影响filter功能
            # ret[v.name] = v.default

            # dynamic filter fields
            if self.select_fields is None or v.name in self.select_fields:
                ret[v.name] = None
        for attr in attributes:
            # attr_define = self.de_attr_map[attr['attributeDefined']]
            attr_name = self.de_attr_map[attr['attributeDefined']].name
            # dynamic filter fields
            if attr_name in ret:
                # if isinstance(attr_define, resource.ForeignKeyAttributeDefined):
                #     ret[attr_name] = self.relate_resources_map.get(attr['value'], attr['value'])
                # else:
                ret[attr_name] = attr['value']
        return ret

    def create(self, validated_data):
        with transaction.atomic():
            attributes = validated_data.pop(PROTECT_ATTRIBUTES, [])
            labels = validated_data.pop('labels', [])
            departments = validated_data.pop('departments', [])
            r = self.Meta.model.objects.create(**validated_data)
            r.departments.set(departments)
            for x in attributes:
                x['resource'] = r
                resourcetype = x.pop('resourcetype')
                a = getattr(attribute, resourcetype)
                if a == attribute.Many2ManyAttribute:
                    value = x.pop('value')
                    for y in value:
                        assert y.type == x['attributeDefined'].relate
                    m2m = a.objects.create(**x)
                    m2m.value.set(value)
                elif a == attribute.ForeignKeyAttribute:
                    assert x['value'] is None or x['value'].type == x['attributeDefined'].relate
                    a.objects.create(**x)
                elif a in (attribute.PKStringAttribute, attribute.PKIntegerAttribute):
                    a.objects.create(atd=x['attributeDefined'].pk, **x)
                else:
                    a.objects.create(**x)
            r.labels.bulk_create([resource.Label(resource=r, **label) for label in labels])
            # create hook
            if r.type.create_hook is not None:
                r.type.create_hook.trigger(self.to_representation(r))
        return r

    def update(self, instance, validated_data):
        umap = {x.attributeDefined: x for x in instance.attributes.all()}
        if instance.type.enable_version_check and validated_data['_version'] != instance._version:
            raise ContentChangedException()
        elif settings.RESOURCE_MODIFY_LOCK and instance.is_locked:
            raise LockedException()
        with transaction.atomic():
            for x in validated_data['attributes']:
                t = umap.get(x['attributeDefined'], None)
                if t is None:
                    try:
                        resourcetype = x.pop('resourcetype')
                        x['resource'] = instance
                        adm = getattr(attribute, resourcetype)
                        if adm == attribute.Many2ManyAttribute:
                            value = x.pop('value')
                            for y in value:
                                assert y.type == x['attributeDefined'].relate
                            m2m = adm.objects.create(**x)
                            m2m.value.set(value)
                        elif adm == attribute.ForeignKeyAttribute:
                            if x['value'] is not None:
                                assert x['value'].type == x['attributeDefined'].relate
                                adm.objects.create(**x)
                        elif adm in (attribute.PKStringAttribute, attribute.PKIntegerAttribute):
                            adm.objects.create(atd=x['attributeDefined'].pk, **x)
                        else:
                            adm.objects.create(**x)
                    except TypeError as err:
                        raise APIException("TypeError: %s is %s %s" % (x['attributeDefined'].name, x['attributeDefined'].__class__.__name__, str(err)))
                else:
                    if t.__class__ == attribute.Many2ManyAttribute:
                        value = x.pop('value')
                        for y in value:
                            assert y.type == x['attributeDefined'].relate
                        t.value.set(value)
                    elif t.__class__ == attribute.ForeignKeyAttribute:
                        if x['value'] is not None:
                            assert x['value'].type == x['attributeDefined'].relate
                        t.value = x['value']
                    elif t.__class__ in (attribute.PKStringAttribute, attribute.PKIntegerAttribute):
                        t.atd = x['attributeDefined'].pk
                        t.value = x['value']
                    else:
                        t.value = x['value']
                    t.save()
            if instance.type.enable_rollback:
                #因为此处无法序列化uuid到json类型里,所以此处进行了类型convert
                bk = self.to_representation(instance)
                for k, v in bk.items() :
                    if isinstance(v, UUID):
                        bk[k] = v.hex
                # 备份与审计
                resource.BackupResource.objects.create(resource_id=instance, version=instance._version, detail=bk)
            labels = validated_data.pop('labels')
            departments = validated_data.pop('departments')
            instance.departments.set(departments)
            instance.labels.all().delete()
            instance.labels.bulk_create([resource.Label(resource=instance, **label) for label in labels])
            instance.name = validated_data.get('name')
            instance.save()
            # update hook
            if instance.type.update_hook is not None:
                instance.type.update_hook.trigger(self.to_representation(instance))
        return instance

    class Meta:
        model = resource.Resource
        fields = ('id', 'name', 'attributes', 'labels',  'departments', '_ctime', '_mtime', '_version')


class BackupResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = resource.BackupResource
        fields = "__all__"


class SimpleResourceSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return {'id': instance.id, 'type': instance.type.name, 'name': instance.name}

    def to_internal_value(self, data):
        ret = OrderedDict()
        ret['id'] = data.get('id')
        return ret

    class Meta:
        model = resource.Resource
        fields = ('id',)