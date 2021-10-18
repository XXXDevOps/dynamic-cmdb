from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from ..serializers import attribute_defined as attribute_defined_serializer
from ..models import attribute_defined as attribute_defined_model
from ..models import attribute_defined


class AttributeTypesApi(APIView):

    def get(self, request):
        for x in attribute_defined.AttributeDefined.__subclasses__():
            print(hasattr(x, 'relate'))
        attribute_types = [{'name':  x.__name__, 'relate': hasattr(x, 'relate')} for x in attribute_defined.AttributeDefined.__subclasses__()]

        return Response(attribute_types)


class AttributeDefinedViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = attribute_defined_model.AttributeDefined.objects.all()
    serializer_class = attribute_defined_serializer.AttributeDefinedSerializer
