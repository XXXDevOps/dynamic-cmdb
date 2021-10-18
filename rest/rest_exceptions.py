from rest_framework.exceptions import APIException
from rest_framework import status
from django.utils.translation import ugettext_lazy as _


class ContentChangedException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = _('content has change, please refresh get latest')
    default_code = 'content has change, please refresh get latest'


class ProtectException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _('you use protect word in your resource define')
    default_code = 'content has change, please refresh get latest'


class LockedException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _('the resource is Locked')
    default_code = 'the resource is Locked, can not modify'
