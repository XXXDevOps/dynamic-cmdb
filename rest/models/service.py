from mptt.models import MPTTModel, TreeForeignKey
from django.db import models, transaction
import copy
from . resource import Resource
import hashlib
from jsonfield import JSONField
from ..protect_keyword import check_name_legal


class Service(MPTTModel):
    name = models.CharField(
        u'name',
        max_length=255,
        blank=False,
        null=False
    )
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        db_constraint=False)
    tree_path_cache = models.CharField(max_length=1024, blank=True, null=True, help_text="不可编辑字段,描述路径缓存")
    tree_path_md5 = models.CharField(max_length=64, blank=True, null=True, help_text="不可编辑字段,描述路径缓存", unique=True)
    env = JSONField('env', blank=True, null=True)
    resources = models.ManyToManyField(Resource, blank=True, db_constraint=False)

    def descendants(self):
        return self.get_descendants(include_self=True)

    def refresh_child_cache(self):
        with transaction.atomic():
            for x in self.descendants():
                x.save()

    def save(self, *args, **kwargs):
        check_name_legal(self.name)
        self.tree_path_cache = self.path(new=False if self.pk else True)
        hash_md5 = hashlib.md5(self.tree_path_cache.encode('utf-8'))
        self.tree_path_md5 = hash_md5.hexdigest()
        super(Service, self).save(*args, **kwargs)

    def path(self, new=False):
        p = []
        if new:
            s = self
            while s.parent:
                p.append(s.name)
                s = s.parent
            p.append(self.name)
            return '.'.join(p)

        for x in self.get_ancestors(ascending=False, include_self=False):
            p.append(x.name)
        p.append(self.name)
        return '.'.join(p)

    def get_env(self, include_self=False):
        fe = {}
        if include_self:
            env = {}
        else:
            env = {k: {
                'value': v,
                'inherit': False,
                'path': self.tree_path_cache,
                'service_id': self.id}
                for k, v in ( self.env if self.env is not None else {}).items()}
        for x in self.get_ancestors(ascending=False, include_self=include_self):
            tmp_env = copy.deepcopy(x.env) if x.env is not None else {}
            tmp_env = {k: {'value': v, 'inherit': True, 'path': x.tree_path_cache, 'service_id': x.id} for k, v in tmp_env.items()}
            fe.update(tmp_env)
        fe.update(env)
        return fe


