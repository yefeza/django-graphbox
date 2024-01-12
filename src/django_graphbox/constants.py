""" 
Global constants for the django_graphbox schema.
"""
import graphene

GRAPHBOX_SUPPORT_FILE_UPLOAD = False
try:
    import graphene_file_upload.scalars

    GRAPHBOX_SUPPORT_FILE_UPLOAD = True
except:
    pass

MODEL_FIELD_TO_GRAPHENE_TYPE = {
    "AutoField": graphene.ID,
    "BigAutoField": graphene.ID,
    "BigIntegerField": graphene.BigInt if hasattr(graphene, "BigInt") else graphene.Int,
    "BooleanField": graphene.Boolean,
    "CharField": graphene.String,
    "DateField": graphene.Date,
    "DateTimeField": graphene.DateTime,
    "DecimalField": graphene.Decimal,
    "DurationField": graphene.String,
    "EmailField": graphene.String,
    "FilePathField": graphene.String,
    "FloatField": graphene.Float,
    "IntegerField": graphene.Int,
    "GenericIPAddressField": graphene.String,
    "PositiveIntegerField": graphene.Int,
    "PositiveSmallIntegerField": graphene.Int,
    "SlugField": graphene.String,
    "SmallIntegerField": graphene.Int,
    "TextField": graphene.String,
    "TimeField": graphene.Time,
    "URLField": graphene.String,
    "UUIDField": graphene.String,
    "ForeignKey": graphene.ID,
    "JSONField": graphene.String,
    "OneToOneField": graphene.ID,
}
if GRAPHBOX_SUPPORT_FILE_UPLOAD:
    MODEL_FIELD_TO_GRAPHENE_TYPE["FileField"] = graphene_file_upload.scalars.Upload
    MODEL_FIELD_TO_GRAPHENE_TYPE["ImageField"] = graphene_file_upload.scalars.Upload

NO_ERROR = 0
UNKNOWN_ERROR = 1
INVALID_CREDENTIALS = 2
INVALID_TOKEN = 3
EXPIRED_TOKEN = 4
INTERNAL_ERROR = 5
ACCESS_DENIED = 6
INSTANCE_NOT_FOUND = 7
INSUFFICIENT_PERMISSIONS = 8
USER_ALREADY_EXISTS = 9
SUSPENDED_USER = 10
BAD_GENERATED_TOKEN = 11
INVALID_CAPTCHA = 12

import operator

OPERATIONS = {
    "=": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "in": operator.contains,
    "not in": lambda x, y: not operator.contains(x, y),
    "like": lambda x, y: y in x,
    "not like": lambda x, y: y not in x,
}
