from django.db import models
from concurrency.fields import IntegerVersionField
from .base import BaseModel
from .hooks import HttpHook


class ResourceDefined(BaseModel):
    _version = IntegerVersionField()
    name = models.CharField(u'resource defined name', max_length=255, blank=False, null=False, unique=True)
    enable_version_check = models.BooleanField(u'concurrency version update check', max_length=255, default=False)
    enable_rollback = models.BooleanField(u'rollback old version', max_length=255, default=False)
    create_hook = models.ForeignKey(HttpHook,
                                    default=None,
                                    null=True,
                                    related_name="create_hook",
                                    blank=True,
                                    on_delete=models.SET_NULL,
                                    db_constraint=False)
    update_hook = models.ForeignKey(HttpHook,
                                    default=None,
                                    null=True,
                                    related_name="update_hook",
                                    blank=True,
                                    on_delete=models.SET_NULL,
                                    db_constraint=False)
    delete_hook = models.ForeignKey(HttpHook,
                                    default=None,
                                    null=True,
                                    related_name="delete_hook",
                                    blank=True,
                                    on_delete=models.SET_NULL,
                                    db_constraint=False)