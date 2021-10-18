"""cmdb URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.urls import path, include
from rest.views import resource, resource_defined, attribute_defined, attribute, sql, base, service, hook
from rest_framework import routers
from rest_framework.documentation import include_docs_urls

router = routers.DefaultRouter()
router.register(r'trace-version', resource.BackupResourceViewSet)
router.register(r'user', base.UserViewSet)
router.register(r'department', base.DepartmentViewSet)
router.register(r'service/tree', service.ServiceTreeViewSet)
router.register(r'service', service.ServiceViewSet)
router.register(r'hook', hook.HookViewSet)
router.register(r'hook-server', hook.HookServerViewSet)
router.register(r'resource-defined', resource_defined.ResourceDefinedViewSet)
router.register(r'attribute-defined', attribute_defined.AttributeDefinedViewSet)
router.register(r'resource/label', resource.LabelKeyViewSet, basename='rs-labels-k')
router.register(r'resource/label/(?P<label_k>[^/.]*)', resource.LabelValueViewSet, basename='rs-labels-v')
router.register(r'(?P<resource_defined>[^/.]+)', resource.ResourceViewSet, basename='rs')
router.register(r'(?P<resource_defined>[^/.]+)/(?P<resource_id>[^/]+)/(?P<m2m_or_fk_attr>[^/]+)',
                resource.ResourceViewSet,
                basename='rs-nest')


v1_urlpatterns = [
    path(r'v1/login/', base.CustomAuthToken.as_view()),
    path(r'v1/sql/', sql.SqlViewSet.as_view()),
    path(r'v1/mine/', base.MineViewSet.as_view(), name="mine"),
    path(r'v1/environment/', base.EnvViewSet.as_view(), name="cmdb-env"),
    path(r'v1/attribute-types/', attribute_defined.AttributeTypesApi.as_view(), name='attribute-types'),
    path('v1/', include(router.urls)),
]

urlpatterns = [
    path('health', base.health),
    path(settings.URL_PREFIX, include(v1_urlpatterns)),
    path(settings.URL_PREFIX+'docs', include_docs_urls(title="CMDB API DOC")),
    path('admin', base.index_view, name='index'),
]
