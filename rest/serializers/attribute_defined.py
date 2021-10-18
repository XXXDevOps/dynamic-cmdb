from rest_framework import serializers
from rest_polymorphic.serializers import PolymorphicSerializer
from ..models import attribute_defined


class IntegerAttributeDefinedSerializer(serializers.ModelSerializer):
    class Meta:
        model = attribute_defined.IntegerAttributeDefined
        fields = "__all__"


class StringAttributeDefinedSerializer(serializers.ModelSerializer):
    class Meta:
        model = attribute_defined.StringAttributeDefined
        fields = "__all__"


class PKIntegerAttributeDefinedSerializer(serializers.ModelSerializer):
    class Meta:
        model = attribute_defined.PKIntegerAttributeDefined
        fields = "__all__"


class PKStringAttributeDefinedSerializer(serializers.ModelSerializer):
    class Meta:
        model = attribute_defined.PKStringAttributeDefined
        fields = "__all__"


class TextAttributeDefinedSerializer(serializers.ModelSerializer):
    class Meta:
        model = attribute_defined.TextAttributeDefined
        fields = "__all__"


class FloatAttributeDefinedSerializer(serializers.ModelSerializer):
    class Meta:
        model = attribute_defined.FloatAttributeDefined
        fields = "__all__"


class ObjectAttributeDefinedSerializer(serializers.ModelSerializer):
    class Meta:
        model = attribute_defined.ObjectAttributeDefined
        fields = "__all__"


class Many2ManyAttributeDefinedSerializer(serializers.ModelSerializer):
    class Meta:
        model = attribute_defined.Many2ManyAttributeDefined
        fields = "__all__"


class ForeignKeyAttributeDefinedSerializer(serializers.ModelSerializer):
    class Meta:
        model = attribute_defined.ForeignKeyAttributeDefined
        fields = "__all__"


class DatetimeAttributeDefinedSerializer(serializers.ModelSerializer):
    class Meta:
        model = attribute_defined.DatetimeAttributeDefined
        fields = "__all__"


class DateAttributeDefinedSerializer(serializers.ModelSerializer):
    class Meta:
        model = attribute_defined.DateAttributeDefined
        fields = "__all__"


class AttributeDefinedSerializer(PolymorphicSerializer):
    model_serializer_mapping = {
        attribute_defined.IntegerAttributeDefined: IntegerAttributeDefinedSerializer,
        attribute_defined.StringAttributeDefined: StringAttributeDefinedSerializer,
        attribute_defined.PKIntegerAttributeDefined: PKIntegerAttributeDefinedSerializer,
        attribute_defined.PKStringAttributeDefined: PKStringAttributeDefinedSerializer,
        attribute_defined.FloatAttributeDefined: FloatAttributeDefinedSerializer,
        attribute_defined.TextAttributeDefined: TextAttributeDefinedSerializer,
        attribute_defined.Many2ManyAttributeDefined: Many2ManyAttributeDefinedSerializer,
        attribute_defined.ObjectAttributeDefined: ObjectAttributeDefinedSerializer,
        attribute_defined.ForeignKeyAttributeDefined: ForeignKeyAttributeDefinedSerializer,
        attribute_defined.DatetimeAttributeDefined: DatetimeAttributeDefinedSerializer,
        attribute_defined.DateAttributeDefined: DateAttributeDefinedSerializer
    }