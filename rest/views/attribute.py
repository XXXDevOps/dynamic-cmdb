from rest_framework import viewsets
from ..serializers import attribute as attribute_serializer
from ..models import attribute as attribute_model


class AttributeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = attribute_model.Attribute.objects.all()
    serializer_class = attribute_serializer.AttributeSerializer
