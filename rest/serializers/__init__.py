from rest_framework import serializers
from ..models import User, Department


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        # fields = '__all__'
        fields = ('id', 'url', 'username', 'name', 'email', 'departments')


class DepartmentSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects, required=False)
    leaders = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects, required=False)

    class Meta:
        model = Department
        fields = "__all__"












