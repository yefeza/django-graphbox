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
    big_integer_field = models.BigIntegerField()
    # BooleanField
    boolean_field = models.BooleanField()
    # CharField
    char_field = models.CharField(max_length=100)
    # DateField
    date_field = models.DateField()
    # DateTimeField
    date_time_field = models.DateTimeField()
    # DecimalField
    decimal_field = models.DecimalField(max_digits=10, decimal_places=2)
    # DurationField
    duration_field = models.DurationField()
    # EmailField
    email_field = models.EmailField()
    # FileField
    file_field = models.FileField()
    # FilePathField
    file_path_field = models.FilePathField()
    # FloatField
    float_field = models.FloatField()
    # ImageField
    image_field = models.ImageField()
    # IntegerField
    integer_field = models.IntegerField()
    # GenericIPAddressField
    generic_ip_address_field = models.GenericIPAddressField()
    # PositiveIntegerField
    positive_integer_field = models.PositiveIntegerField()
    # PositiveSmallIntegerField
    positive_small_integer_field = models.PositiveSmallIntegerField()
    # SlugField
    slug_field = models.SlugField()
    # SmallIntegerField
    small_integer_field = models.SmallIntegerField()
    # TextField
    text_field = models.TextField()
    # TimeField
    time_field = models.TimeField()
    # URLField
    url_field = models.URLField()
    # UUIDField
    uuid_field = models.UUIDField()
    # ForeignKey
    foreign_field = models.ForeignKey(RelatedModel, on_delete=models.CASCADE, related_name='pruebas')
