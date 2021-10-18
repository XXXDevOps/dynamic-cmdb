from django.db import models
from polymorphic.models import PolymorphicManager
from jsonfield import JSONField
from .base import BaseModel
from .resource_defined import ResourceDefined
from . import PolymorphicModel
from ..protect_keyword import PROTECT_NAME_LIST
from ..rest_exceptions import ProtectException


class AttributeDefined(PolymorphicModel, BaseModel):
    name = models.CharField('attribute define name', max_length=64, blank=False, null=False)
    resourceDefined = models.ForeignKey(
        ResourceDefined,
        db_constraint=False,
        on_delete=models.CASCADE,
        default=None,
        blank=False,
        related_name='attributes')
    objects = PolymorphicManager()

    def save(self, *args, **kwargs):
        if self.name in PROTECT_NAME_LIST:
            raise ProtectException("'%s' is a protect keyword" % self.name)
        super(AttributeDefined, self).save(*args, **kwargs)


class IntegerAttributeDefined(AttributeDefined):
    default = models.IntegerField('value', blank=True, null=True)


class PKIntegerAttributeDefined(AttributeDefined):
    default = models.IntegerField('value', blank=True, null=True)


class StringAttributeDefined(AttributeDefined):
    default = models.CharField('value', max_length=255, blank=True, null=True)


class PKStringAttributeDefined(AttributeDefined):
    default = models.CharField('value', max_length=255, blank=True, null=True)


class TextAttributeDefined(AttributeDefined):
    default = models.TextField('value', blank=True, null=True)


class FloatAttributeDefined(AttributeDefined):
    default = models.FloatField('value', blank=True, null=True)


class ObjectAttributeDefined(AttributeDefined):
    default = JSONField('value', blank=True, null=True)


class DatetimeAttributeDefined(AttributeDefined):
    default = models.DateTimeField('value', blank=True, null=True)


class DateAttributeDefined(AttributeDefined):
    default = models.DateField('value', blank=True, null=True)


class Many2ManyAttributeDefined(AttributeDefined):
    relate = models.ForeignKey(
        ResourceDefined,
        db_constraint=False,
        on_delete=models.CASCADE,
        null=False,)


class ForeignKeyAttributeDefined(AttributeDefined):
    relate = models.ForeignKey(
        ResourceDefined,
        db_constraint=False,
        on_delete=models.CASCADE,
        null=False,)