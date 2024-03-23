# models
from django.db import models


# Create your models here.
class FailedLoginAttempt(models.Model):
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    request_metadata = models.TextField(null=True)
    session_key = models.CharField(max_length=255, null=True)
    user_id = models.IntegerField(null=True)


class JsonWebToken(models.Model):
    creation_time = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    inactive_time = models.DateTimeField(null=True)
    token = models.TextField()
    request_metadata = models.TextField(null=True)
    session_key = models.CharField(max_length=255, null=True)
    user_id = models.IntegerField()


class LoginCaptcha(models.Model):
    creation_time = models.DateTimeField(auto_now_add=True)
    captcha_id = models.CharField(max_length=255, unique=True)
    captcha_value = models.CharField(max_length=25)
    active = models.BooleanField(default=True)
    image_generated = models.BooleanField(default=False)
    session_key = models.CharField(max_length=255, null=True)
    user_id = models.IntegerField(null=True)
