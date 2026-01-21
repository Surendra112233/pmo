from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, (InvalidToken, TokenError)):
        return Response({
            "success": False,
            "message": "Token expired",
            "error": {
                "code": 401,
                "details": "Your session has expired. Please log in again."
            }
        }, status=status.HTTP_401_UNAUTHORIZED)

    return response
