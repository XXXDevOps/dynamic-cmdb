from rest_framework import viewsets
from rest_framework.decorators import action
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import Department, User
from .. import serializers
import logging
from ..version import VERSION_STRING
from django.db.models import Lookup
from django.db.models.fields import Field
from django.views.decorators.http import require_http_methods
from django.shortcuts import HttpResponse


class NotEqual(Lookup):
    lookup_name = 'ne'

    def as_sql(self, qn, connection):
        lhs, lhs_params = self.process_lhs(qn, connection)
        rhs, rhs_params = self.process_rhs(qn, connection)
        params = lhs_params + rhs_params
        return '%s != %s' % (lhs, rhs), params


# 注册not equal
Field.register_lookup(NotEqual)
logger = logging.getLogger('audit')
index_view = never_cache(TemplateView.as_view(template_name='index.html'))


#健康检查接口
@require_http_methods(['GET'])
def health(request):
    return HttpResponse("ok")


class EnvViewSet(APIView):

    def get(self, request):
        return Response({'version': VERSION_STRING})


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk
        })


class MineViewSet(APIView):

    def get(self, request):
        user = self.request.user
        serializer_context = {
            'request': request,
        }
        serializer = serializers.UserSerializer(user, context=serializer_context)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = serializers.UserSerializer

    @action(methods=['get'], detail=True)
    def expend_department_nodes(self, request, *args, **kwargs):
        u = self.get_object()
        serializer_context = {
            'request': request,
        }
        serializer = serializers.DepartmentSerializer(u.expend_department_nodes(), context=serializer_context, many=True)
        return Response(serializer.data)


# Create your views here.
class DepartmentViewSet(viewsets.ModelViewSet):
    # authentication_classes = (authentication.JWTAuthentication,)
    # permission_classes = (permissions.IsAuthenticated,)
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Department.objects.all()
    serializer_class = serializers.DepartmentSerializer
