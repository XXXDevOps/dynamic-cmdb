from django.db import models
from jsonfield import JSONField
from concurrency.fields import IntegerVersionField
from django_redis import get_redis_connection
from datetime import datetime, timedelta
from .base import BaseModel
from . import Department
from .resource_defined import ResourceDefined
from .. import rest_exceptions


class Resource(BaseModel):
    id = models.UUIDField(auto_created=True, primary_key=True, default=BaseModel.gen_uuid, editable=False)
    name = models.CharField(u'resource defined name', max_length=255, blank=False, null=False)
    type = models.ForeignKey(ResourceDefined, db_constraint=False, on_delete=models.CASCADE)
    departments = models.ManyToManyField(Department, blank=True)
    _version = IntegerVersionField()

    def lock(self, system, token=None, expire=60, exclusive=False):
        conn = get_redis_connection('default')
        if exclusive:
            key = '%s@%s@exclusive' % (self.id, system)
            if conn.setnx(name=key, value=token if token is not None else 'null'):
                conn.expire(name=key, time=expire)
            else:
                raise rest_exceptions.LockedException
        else:
            delta = timedelta(seconds=expire)
            now = datetime.now()
            furture_trs = (now+delta).strftime('%Y-%m-%d@%H:%M:%S')
            key = '%s@%s@%s' % (self.id, system, furture_trs)
            conn.setex(name=key, value=token if token is not None else 'null', time=expire)
        return

    def unlock(self, system, token=None):
        conn = get_redis_connection('default')
        keys_pattern = '%s@%s@*' % (self.id, system)
        keys = conn.keys(keys_pattern)
        for key in keys:
            conn.delete(key)
        return

    @property
    def is_locked(self):
        return len(self.get_locks()) > 0

    def get_locks(self, system=None):
        conn = get_redis_connection('default')
        ls = conn.keys('%s@%s@*' % (self.id, system if system is not None else '*'))
        return ls

    class Meta:
        ordering = ['_ctime']
        unique_together = ('type', 'name')


class Label(models.Model):
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name='labels'
    )
    k = models.CharField(u'k', max_length=255, blank=False, null=False)
    v = models.CharField(u'v', max_length=255, blank=False, null=False)

    class Meta:
        unique_together = ["resource", "k", "v"]
        index_together = ["resource", "k", "v"]

    def __unicode__(self):
        return '%s: %s' % (self.k, self.v)


class BackupResource(BaseModel):
    version = models.BigIntegerField(auto_created=True)
    resource_id = models.ForeignKey(Resource, on_delete=models.DO_NOTHING, db_constraint=False)
    detail = JSONField()


class ResourceEnv(models.Model):
    resource = models.ForeignKey(Resource, db_constraint=False, on_delete=models.CASCADE, unique=True)
    env = JSONField()
    _mtime = models.DateTimeField(auto_now=True)
