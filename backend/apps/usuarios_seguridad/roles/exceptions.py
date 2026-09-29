"""
Excepciones de dominio para la gestión de roles y permisos (CU4).
"""
from rest_framework import status
from rest_framework.exceptions import APIException


class OperacionInvalidaError(APIException):
    """
    Se lanza cuando una operación sobre roles o la matriz de permisos viola una regla de seguridad.
    Equivale a HTTP 400 Bad Request.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Operación sobre roles o permisos no permitida por reglas de seguridad.'
    default_code = 'operacion_invalida'
