from django.db import models
from jsonfield import JSONField
from polymorphic.models import PolymorphicManager
from .attribute_defined import AttributeDefined
from . import PolymorphicModel


class Attribute(PolymorphicModel):
    attributeDefined = models.ForeignKey(AttributeDefined, db_constraint=False, on_delete=models.CASCADE)
    resource = models.ForeignKey('Resource', db_constraint=False, on_delete=models.CASCADE, related_name='attributes', blank=True)
    objects = PolymorphicManager()


class IntegerAttribute(Attribute):
    value = models.IntegerField('value', blank=True, null=True, default=None)


class StringAttribute(Attribute):
    value = models.CharField('value', max_length=255, blank=True, null=True, default=None)


class PKIntegerAttribute(Attribute):
    atd = models.IntegerField("atd", null=False, default=None)
    value = models.IntegerField('value', blank=True,  default=None, null=True)

    class Meta:
        unique_together = (("atd", "value"),)


class PKStringAttribute(Attribute):
    atd = models.IntegerField("atd", null=False, default=None)
    value = models.CharField('value', max_length=255, blank=True, null=True)

    class Meta:
        unique_together = (("atd", "value"),)


class TextAttribute(Attribute):
    value = models.TextField('value', blank=True, null=True, default=None)


class FloatAttribute(Attribute):
    value = models.FloatField('value', blank=True, null=True, default=None)


class ObjectAttribute(Attribute):
    value = JSONField('value', blank=True, null=True, default=None)


class DatetimeAttribute(Attribute):
    value = models.DateTimeField('value', blank=True, null=True, default=None)


class DateAttribute(Attribute):
    value = models.DateField('value', blank=True, null=True, default=None)


class Many2ManyAttribute(Attribute):
    value = models.ManyToManyField(
        'Resource', blank=True)


class ForeignKeyAttribute(Attribute):
    value = models.ForeignKey(
        'Resource',
        db_constraint=False,
        null=True,
        on_delete=models.SET_NULL,
        default=None)