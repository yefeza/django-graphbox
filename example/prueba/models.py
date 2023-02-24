from django.db import models
from django.conf import settings

# Create your models here.

class CustomUser(models.Model):
    VALID_ROLES = [
        (settings.ROL_SOPORTE, 'SOPORTE'),
        (settings.ROL_RESPONSABLE, 'RESPONSABLE'),
        (settings.ROL_AUXILIAR, 'AUXILIAR'),
    ]
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.TextField()
    is_active = models.BooleanField(default=True)
    rol = models.CharField(max_length=100, choices=VALID_ROLES)
    foto = models.ImageField(upload_to='fotos', null=True, blank=True)
    social_id = models.CharField(max_length=100, null=True, blank=True)
    social_origin = models.CharField(max_length=100, null=True, blank=True)
    
class RelatedModel(models.Model):
    title = models.CharField(max_length=100)
    text = models.TextField()

class Prueba(models.Model):
    # model with all datatypes supported by django_graphbox
    '''
        MODEL_FIELD_TO_GRAPHENE_TYPE = {
            'AutoField': graphene.ID,
            'BigAutoField': graphene.ID,
            'BigIntegerField': graphene.Int,
            'BooleanField': graphene.Boolean,
            'CharField': graphene.String,
            'DateField': graphene.Date,
            'DateTimeField': graphene.DateTime,
            'DecimalField': graphene.Decimal,
            'DurationField': graphene.String,
            'EmailField': graphene.String,
            'FileField': graphene_file_upload.scalars.Upload,
            'FilePathField': graphene.String,
            'FloatField': graphene.Float,
            'ImageField': graphene_file_upload.scalars.Upload,
            'IntegerField': graphene.Int,
            'GenericIPAddressField': graphene.String,
            'PositiveIntegerField': graphene.Int,
            'PositiveSmallIntegerField': graphene.Int,
            'SlugField': graphene.String,
            'SmallIntegerField': graphene.Int,
            'TextField': graphene.String,
            'TimeField': graphene.Time,
            'URLField': graphene.String,
            'UUIDField': graphene.String,
            'ForeignKey': graphene.ID
        }
    '''
    # BigIntegerField
    big_integer_field = models.BigIntegerField(null=True, blank=True)
    # BooleanField
    boolean_field = models.BooleanField(null=True, blank=True)
    # CharField
    char_field = models.CharField(max_length=100)
    # DateField
    date_field = models.DateField(null=True, blank=True)
    # DateTimeField
    date_time_field = models.DateTimeField(null=True, blank=True)
    # DecimalField
    decimal_field = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # DurationField
    duration_field = models.DurationField(null=True, blank=True)
    # EmailField
    email_field = models.EmailField(null=True, blank=True)
    # FileField
    file_field = models.FileField(null=True, blank=True)
    # FilePathField
    file_path_field = models.FilePathField(null=True, blank=True)
    # FloatField
    float_field = models.FloatField(null=True, blank=True)
    # ImageField
    image_field = models.ImageField(null=True, blank=True)
    # IntegerField
    integer_field = models.IntegerField(null=True, blank=True)
    # GenericIPAddressField
    generic_ip_address_field = models.GenericIPAddressField(null=True, blank=True)
    # PositiveIntegerField
    positive_integer_field = models.PositiveIntegerField(null=True, blank=True)
    # PositiveSmallIntegerField
    positive_small_integer_field = models.PositiveSmallIntegerField(null=True, blank=True)
    # SlugField
    slug_field = models.SlugField(null=True, blank=True)
    # SmallIntegerField
    small_integer_field = models.SmallIntegerField(null=True, blank=True)
    # TextField
    text_field = models.TextField(null=True, blank=True)
    # TimeField
    time_field = models.TimeField(null=True, blank=True)
    # URLField
    url_field = models.URLField(null=True, blank=True)
    # UUIDField
    uuid_field = models.UUIDField(null=True, blank=True)
    # ForeignKey
    foreign_field = models.ForeignKey(RelatedModel, on_delete=models.CASCADE, related_name='pruebas')
