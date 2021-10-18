from .rest_exceptions import ProtectException
PROTECT_ATTRIBUTES = 'attributes'
PROTECT_MODIFY_USER = '_modify_user'
PROTECT_NAME_LIST = ['name', 'search', 'groupby', 'distinct', 'count', PROTECT_ATTRIBUTES, PROTECT_MODIFY_USER]
PROTECT_CHARACTER = ['.']


def check_name_legal(name):
    for x in PROTECT_CHARACTER:
        if x in name:
            raise ProtectException(detail='\'%s\' is protect character.')
