'''
Script to create a CustomUser
'''
from prueba.models import CustomUser
from django.contrib.auth.hashers import make_password
from django.conf import settings

def run():
    if not CustomUser.objects.filter(name='admin').exists():
        CustomUser.objects.create(
            name='admin', 
            email='admin@example.com',
            password=make_password('admin'),
            rol=settings.ROL_SOPORTE,
            is_active=True
        )
        print('User created')
