from rest_framework.exceptions import APIException
from rest_framework import status


class TravelRequestException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "travel_request_error"

    def __init__(self, message, status_code=None):
        self.detail = {"message": message}
        if status_code:
            self.status_code = status_code
