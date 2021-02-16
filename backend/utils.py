from rest_framework.response import Response
from functools import wraps
from rest_framework import status

def post_fields(key_list):
    def internal_decorator(f):
        @wraps(f)
        def wrapper(request,*args, **kwds):
            if not all(k in request.data for k in key_list):
                return Response('POST request missing fields',status=status.HTTP_400_BAD_REQUEST)
            return f(request,*args,**kwds)
        return wrapper
    return internal_decorator