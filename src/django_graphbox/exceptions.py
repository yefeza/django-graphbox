""" Error responses for GraphBox API """

from graphene_django.types import ObjectType
import graphene
from .constants import *


class ErrorMsgType(ObjectType):
    """Custom ObjectType to manage the exceptions of the django_graphbox schema."""

    codigo = graphene.Int()
    message = graphene.String()
    description = graphene.String()


class ErrorManager:
    """Class to manage the exceptions of the django_graphbox schema."""

    _error_list = {
        NO_ERROR: {
            "message": "Operación ejecutada correctamente",
            "description": "No ha ocurrido ningún error",
        },
        UNKNOWN_ERROR: {
            "message": "Error desconocido",
            "description": "Ha ocurrido un error desconocido",
        },
        INVALID_CREDENTIALS: {
            "message": "Credenciales inválidas",
            "description": "Las credenciales proporcionadas no son válidas",
        },
        INVALID_TOKEN: {
            "message": "Token inválido",
            "description": "El token proporcionado no es válido",
        },
        EXPIRED_TOKEN: {
            "message": "Token expirado",
            "description": "El token proporcionado ha expirado",
        },
        INTERNAL_ERROR: {
            "message": "Error interno",
            "description": "Ha ocurrido un error interno",
        },
        ACCESS_DENIED: {
            "message": "Acceso denegado",
            "description": "No tiene permisos para realizar esta acción",
        },
        INSTANCE_NOT_FOUND: {
            "message": "Instancia no encontrada",
            "description": "No se ha encontrado la instancia solicitada",
        },
        INSUFFICIENT_PERMISSIONS: {
            "message": "Permisos insuficientes",
            "description": "No tiene permisos suficientes para realizar esta acción",
        },
        USER_ALREADY_EXISTS: {
            "message": "El usuario ya esta en uso.",
            "description": "Esta cuenta de usuario ya fue registrada.",
        },
        SUSPENDED_USER: {
            "message": "Usuario suspendido",
            "description": "El usuario ha sido suspendido. Contacte con el administrador.",
        },
        BAD_GENERATED_TOKEN: {
            "message": "Token generado incorrectamente",
            "description": "El token generado no es válido",
        },
        INVALID_CAPTCHA: {
            "message": "Captcha inválido",
            "description": "El captcha proporcionado no es válido",
        },
    }

    @classmethod
    def get_error_by_code(
        cls, error_code=None, custom_message=None, custom_description=None
    ):
        """Method to get the error message by code.

        Args:
            error_code (int): Code of the error.
            custom_message (str): Custom message to replace the default message.
            custom_description (str): Custom description to replace the default description.

        Returns:
            ErrorMsgType: Error message.
        """
        if error_code is None:
            error_code = UNKNOWN_ERROR
        if custom_message != None and custom_description != None:
            return ErrorMsgType(
                codigo=error_code,
                message=custom_message,
                description=custom_description,
            )
        else:
            if error_code not in cls._error_list.keys():
                error_code = UNKNOWN_ERROR
            return ErrorMsgType(
                codigo=error_code,
                message=cls._error_list[error_code]["message"],
                description=cls._error_list[error_code]["description"],
            )
