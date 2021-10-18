from mptt.models import MPTTModel, TreeForeignKey
from django.db import models
from django.contrib.auth.models import AbstractUser
from polymorphic.models import PolymorphicModel
from django.contrib.contenttypes.models import ContentType

__all__ = ['base']

PolymorphicModel.polymorphic_ctype = models.ForeignKey(
        ContentType,
        null=True,
        editable=False,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="polymorphic_%(app_label)s.%(class)s_set+",
    )


class Department(MPTTModel):
    name = models.CharField(u'name', max_length=32, blank=False, null=False)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', db_constraint=False)
    leaders = models.ManyToManyField("User", related_name="leader_ships", default=[])

    def descendants(self):
        return self.get_descendants(include_self=True)


class User(AbstractUser):
    name = models.CharField(u'name', max_length=32, blank=False, null=False)
    departments = models.ManyToManyField(Department, related_name="members", blank=True, db_constraint=False)

    def expend_department_nodes(self):
        return self.departments.all().get_descendants(include_self=True)


class DepartmentLabel(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, db_constraint=False, related_name='labels')
    k = models.CharField(u'k', max_length=64, blank=False, null=False)
    v = models.CharField(u'v', max_length=64, blank=False, null=False)

    class Meta:
        unique_together = ["department", "k", "v"]
        index_together = ["department", "k", "v"]

    def __unicode__(self):
        return '%s: %s' % (self.k, self.v)


class UserLabel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_constraint=False, related_name='labels')
    k = models.CharField(u'k', max_length=64, blank=False, null=False)
    v = models.CharField(u'v', max_length=64, blank=False, null=False)

    class Meta:
        unique_together = ["user", "k", "v"]
        index_together = ["user", "k", "v"]

    def __unicode__(self):
        return '%s: %s' % (self.k, self.v)