import moz_sql_parser
import pyparsing
from rest_framework.exceptions import APIException
from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import resource
from ..serializers.resource import ResourceSerializer
from .resource import ResourceViewSet


class SqlViewSet(APIView):

    def get(self, request):
        sql = request.data.get('sql', None)
        try:
            sql_parse = moz_sql_parser.parse(sql)
        except pyparsing.ParseException as e:
            raise APIException(str(e))
        rd_name = sql_parse.get('from')
        columns = sql_parse.get('select')
        where = sql_parse.get('where')
        if columns == '*':
            select_fields = None
        elif isinstance(columns, dict):
            select_fields = [columns.get('value')]
        elif isinstance(columns, list):
            select_fields = [ x.get('value') for x in columns]
        else:
            raise APIException('sql column unexpect error')
        rd = resource.ResourceDefined.objects.get(name=rd_name)
        r = resource.Resource.objects.filter(type=rd)
        where_conditions = {}
        # 后续补充sql where条件功能
        if where:
            if isinstance(where, dict):
                pass
        attr_map = {
            x.name: (
                x.id,
                ResourceViewSet.get_attribute_classname_by_attribute_defined(x.__class__.__name__),
                x
            ) for x in rd.attributes.all()
        }
        de_attr_map = {x.id: x for x in rd.attributes.all()}
        # self.select_fields = kwargs.pop('select_fields', None)
        s = ResourceSerializer(resourceDefined=rd, attr_map=attr_map, de_attr_map=de_attr_map, select_fields=select_fields, many=True)
        return Response(s.to_representation(r))



