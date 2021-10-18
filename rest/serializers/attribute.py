from rest_framework import serializers
from rest_polymorphic.serializers import PolymorphicSerializer
from django.conf import settings
from rest_framework.exceptions import ValidationError
from collections import OrderedDict
from ..models import attribute, resource


class IntegerAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = attribute.IntegerAttribute
        fields = "__all__"


class StringAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = attribute.StringAttribute
        fields = "__all__"


class PKIntegerAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = attribute.PKIntegerAttribute
        fields = "__all__"


class PKStringAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = attribute.PKStringAttribute
        fields = "__all__"

    def to_internal_value(self, data):
        data['attributeDefined'] = self.root.de_attr_map.get(data['attributeDefined'])
        return data


class TextAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = attribute.TextAttribute
        fields = "__all__"


class FloatAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = attribute.FloatAttribute
        fields = "__all__"


class ObjectAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = attribute.ObjectAttribute
        fields =  "__all__"


class Many2ManyAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = attribute.Many2ManyAttribute
        fields = "__all__"

    def to_representation(self, instance):
        if instance.value:
            v = [x['name'] for x in instance.value.values()]
        else:
            v = None
        return OrderedDict({'value': v, 'resourcetype': instance.__class__.__name__, 'attributeDefined': instance.attributeDefined.id})

    def to_internal_value(self, data):
        atd = self.root.de_attr_map.get(data.get('attributeDefined'))
        ret = OrderedDict()
        if data['value'] is None:
            ret['value'] = []
        else:
            try:
                instance = resource.Resource.objects.filter(name__in=data['value'], type=atd.relate)
            except resource.Resource.DoesNotExist:
                raise ValidationError({
                    atd.name: ["no such foreign key named %s" % data['value']]
                }, code='invalid')
            ret['value'] = instance
        ret['attributeDefined'] = atd
        return ret


class ForeignKeyAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = attribute.ForeignKeyAttribute
        fields = "__all__"

    def to_representation(self, instance):
        if instance.value:
            v = instance.value.name
        else:
            v = None
        return OrderedDict({'value': v, 'resourcetype': instance.__class__.__name__, 'attributeDefined': instance.attributeDefined.id})

    def to_internal_value(self, data):
        atd = self.root.de_attr_map.get(data.get('attributeDefined'))
        ret = OrderedDict()

        if data['value'] is not None:
            try:
                instance = resource.Resource.objects.get(name=data['value'], type=atd.relate)
            except resource.Resource.DoesNotExist:
                raise ValidationError({
                    atd.name: ["no such foreign key named %s" % data['value']]
                }, code='invalid')
            ret['value'] = instance
        else:
            ret['value'] = None
        ret['attributeDefined'] = atd
        return ret


class DatetimeAttributeSerializer(serializers.ModelSerializer):
    value = serializers.DateTimeField(format=settings.DATETIME_FORMAT)

    class Meta:
        model = attribute.DatetimeAttribute
        fields = "__all__"


class DateAttributeSerializer(serializers.ModelSerializer):
    value = serializers.DateField(format=settings.DATE_FORMAT)

    class Meta:
        model = attribute.DateAttribute
        fields = "__all__"


class AttributeSerializer(PolymorphicSerializer):
    model_serializer_mapping = {
        attribute.IntegerAttribute: IntegerAttributeSerializer,
        attribute.StringAttribute: StringAttributeSerializer,
        attribute.PKIntegerAttribute: PKIntegerAttributeSerializer,
        attribute.PKStringAttribute: PKStringAttributeSerializer,
        attribute.FloatAttribute: FloatAttributeSerializer,
        attribute.TextAttribute: TextAttributeSerializer,
        attribute.ObjectAttribute: ObjectAttributeSerializer,
        attribute.Many2ManyAttribute: Many2ManyAttributeSerializer,
        attribute.ForeignKeyAttribute: ForeignKeyAttributeSerializer,
        attribute.DatetimeAttribute: DatetimeAttributeSerializer,
        attribute.DateAttribute: DateAttributeSerializer,
    }