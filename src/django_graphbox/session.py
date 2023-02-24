""" This module implements a Session Manager JWT based, that can be used on SchemaBuilder for authentication.
"""
# jwt
import jwt
# settings import
from django.conf import settings
# randomic session id generator
from uuid import uuid4
# time management import
from django.utils import timezone as tz
import datetime
# django password validator
from django.contrib.auth.hashers import check_password
# error manager
from .exceptions import ErrorManager
# global constants
from .constants import *
# google imports
from google.oauth2 import id_token
from google.auth.transport import requests as grq
# facebook imports
import facebook
# files manage
from django.core.files.images import ImageFile
from django.core.files.temp import tempfile
import requests
from .hasher import HashManager
from moodle import Moodle

class GroupManager:
    """ Manager for allow access to users by groups. """
    _groups={}
    _modify_permissions={}
    _user_model=None
    _rol_field_name='rol'

    def __init__(self, user_model, rol_field_name, groups={}, modify_permissions={}):
        """ Initialize the GroupManager.
        
        Args:
            user_model (class): The user model class.
            rol_field_name (str): The name of the field that contains the user rol.
            groups (dict): The groups and their user rol list. {'group_name': ['rol_1', 'rol_2', ...], ...}
            modify_permissions (dict): The user rol and their modify permissions for change data of other users. {'rol_1': ['rol_1', 'rol_2', ...], ...}
        """
        self._user_model=user_model
        self._rol_field_name=rol_field_name
        self._groups=groups
        self._modify_permissions=modify_permissions

    def add_group(self, group_name, access_list):
        """ Add a new group to the manager. """
        self._groups[group_name]=access_list

    def validar_acesso(self, user_instance, group_name):
        """ Validate if a user_instance is on a group_name. """
        if self._user_model!=None and isinstance(user_instance, self._user_model):
            if hasattr(user_instance, self._rol_field_name):
                if group_name=='all' or getattr(user_instance, self._rol_field_name) in self._groups[group_name]:
                    return True
                return False
    
    def get_modify_permissions(self, user_instance):
        """ Get the modify permissions for a user_instance. """
        if user_instance.rol in self._modify_permissions:
            return self._modify_permissions[user_instance.rol]
        return []

class GoogleSession:
    client_id=getattr(settings, 'GOOGLE_CLIENT_ID', None)
    @classmethod
    def validate (cls, token):
        try:
            info=id_token.verify_oauth2_token(token, grq.Request(), cls.client_id)
            return True, info
        except:
            data=[]
            return False,data

class FacebookSession:
    app_id=getattr(settings, 'FACEBOOK_APP_ID', None)
    @classmethod
    def validate (cls, token):
        try:
            graph=facebook.GraphAPI(access_token=token, version='3.1')
            info=graph.get_object('me', fields='id,email,name,picture')
            return True, info
        except:
            data=[]
            return False,data

class Manager:
    _security_key=settings.SECRET_KEY
    social_origin_facebook='FACEBOOK'
    social_origin_google='GOOGLE'

    def __init__(self, user_model, session_key=None, use_social_session=False, rol_field_name='rol', login_id_field_name='uname', password_field_name='password', name_field_name="name", photo_field_name="photo", social_id_field=None, social_origin_field=None, active_field_name=None, session_expiration_time=12, groups={}, modify_permissions={}, security_key=None, moodle_urls=[], moodle_auth_field_name='username', moodle_id_field_name='email'):
        """Session Manager for a user_model

        Args:
            user_model (django.models.Model): User model
            session_key (str, optional): Session key to identify the session. Defaults to None for only one schema.
            use_social_session (bool, optional): Use social session. Defaults to False.
            rol_field_name (str, optional): Field name of user model for access level control. Defaults to 'rol'.
            login_id_field_name (str, optional): Field name of unique field used for authentication. Defaults to 'uname'.
            password_field_name (str, optional): Field name of password field used for authentication. Defaults to 'password'.
            name_field_name (str, optional): Field name of name field used for authentication. Defaults to 'name'. (Only for social login)              
            photo_field_name (str, optional): Field name of photo field used for authentication. Defaults to 'photo'. (Only for social login)
            social_id_field (str, optional): Field name of social id field used for authentication. Defaults to None. (Only for social login)
            social_origin_field (str, optional): Field name of social origin field used for authentication. Defaults to None. (Only for social login)
            active_field_name (str, optional): Field name for boolean field name for validation active user. Defaults to None for not validation.
            session_expiration_time (int, optional): Time in hours to set expiration time on jwt. Defaults to 12.
            groups (dict, optional): Predefined access groups {"group_name":["rol_1", "rol_2", "rol_3"]}. Defaults to {}.
            modify_permissions (dict, optional): Predefined modify permissions {"rol_1":["rol_1", "rol_2", "rol_3"]}. Defaults to {}.
            security_key (str, optional): Secret used as secret for sign on jwt. Defaults to None for use django.conf.settings.SECRET_KEY.
            moodle_urls (list, optional): List of dictionaries with moodle urls and token. Defaults to [].
            moodle_auth_field_name (str, optional): Field name of moodle user model for authentication. Defaults to 'username'.
            moodle_id_field_name (str, optional): Field name of moodle user model for identification. Defaults to 'email'.
        """
        id_attribute=user_model._meta.get_field(login_id_field_name)
        if id_attribute.unique==False:
            raise Exception('Field '+login_id_field_name+' must be unique')
        self.user_model=user_model
        self.session_key=session_key
        self.use_social_session=use_social_session
        self.rol_field_name=rol_field_name
        self.login_id_field_name=login_id_field_name
        self.password_field_name=password_field_name
        self.name_field_name=name_field_name
        self.photo_field_name=photo_field_name
        self.social_id_field=social_id_field
        self.social_origin_field=social_origin_field
        self.active_field_name=active_field_name
        self.session_expiration_time=session_expiration_time
        self.group_manager=GroupManager(user_model, rol_field_name, groups, modify_permissions)
        if security_key!=None:
            self._security_key=security_key
        self.moodle_urls=moodle_urls
        self.moodle_auth_field_name=moodle_auth_field_name
        self.moodle_id_field_name=moodle_id_field_name
    
    def _generate_token(self, user_instance, expiration_time=0):
        """Generate jwt for user_instance

        Args:
            user_instance (user_model.__class__): user instance to generate token
            expiration_time (int, optional): expiration time in hours. Defaults to 0 for no expiration.
        Returns:
            str: generated token
        """
        if self.user_model!=None and isinstance(user_instance, self.user_model):
            if hasattr(user_instance, self.rol_field_name):
                session_id=str(uuid4())
                payload={
                    'session_id':session_id,
                    'u_id': user_instance.id,
                }
                if self.session_key!=None:
                    payload['session_key']=self.session_key
                if expiration_time>0:
                    payload['exp']=tz.localtime()+datetime.timedelta(hours=expiration_time)
                return jwt.encode(payload, self._security_key, algorithm='HS256')
        return None
    
    def validate_access(self, request, group_name):
        """Validate access

        Args:
            request (django.http.request.HttpRequest): request to validate Authorization header as Bearer token
            group_name (str): group name to validate
        Returns:
            tuple:(status (bool), user_instance (UserObject))
        """
        if group_name=='open' or group_name==None:
            return True, None, ErrorManager.get_error_by_code(NO_ERROR)
        if 'Authorization' in request.headers:
            token=request.headers['Authorization']
            token=token[7:len(token)]
            try:
                payload=jwt.decode(token, self._security_key, algorithms=['HS256'])
                if self.session_key==None or self.session_key==payload['session_key']:
                    if self.user_model.objects.filter(id=payload['u_id']).exists():
                        user_instance=self.user_model.objects.get(id=payload['u_id'])
                        if self.group_manager.validar_acesso(user_instance, group_name):
                            # import django_auditor_logs if exists
                            if 'django_auditor_logs' in settings.INSTALLED_APPS:
                                try:
                                    from django_auditor_logs.metadata import MetadataManager
                                    user_metadata={}
                                    for field in user_instance._meta.get_fields():
                                        if not field.is_relation:
                                            user_metadata[field.name]=getattr(user_instance, field.name)
                                    MetadataManager.set_user_metadata(user_metadata)
                                except Exception as e:
                                    print(e)
                            return True, user_instance, ErrorManager.get_error_by_code(NO_ERROR)
                        else:
                            return False, None, ErrorManager.get_error_by_code(ACCESS_DENIED)
                    else:
                        return False, None, ErrorManager.get_error_by_code(INVALID_CREDENTIALS)
                else:
                    return False, None, ErrorManager.get_error_by_code(INVALID_TOKEN)
            except:
                return False, None, ErrorManager.get_error_by_code(INVALID_TOKEN)
        else:
            return False, None, ErrorManager.get_error_by_code(INVALID_TOKEN)

    def _auth_with_moodle(self, login_id, password):
        """Validate user with moodle

        Args:
            login_id (str): login id
            password (str): password

        Returns:
            tuple:(status (bool), user_instance (UserObject))
        """
        for moodle_data in self.moodle_urls:
            try:
                response=requests.post(moodle_data['url']+'/login/token.php', data={'username':login_id, 'password':password, 'service':'moodle_mobile_app'})
                if response.status_code==200:
                    token=response.json()['token'] #validate only if token exists
                    moodle = Moodle(moodle_data['url']+"/webservice/rest/server.php", moodle_data['token'])
                    # get user info
                    data_user=moodle('core_user_get_users_by_field', field=self.moodle_auth_field_name, values=[login_id])
                    if len(data_user)>0:
                        data_user=data_user[0]
                        if self.user_model.objects.filter(**{self.login_id_field_name:data_user[self.moodle_id_field_name]}).exists():
                            user_instance=self.user_model.objects.get(**{self.login_id_field_name:data_user[self.moodle_id_field_name]})
                            return True, user_instance
                        else:
                            user_instance=self.user_model(**{self.social_id_field:id, self.name_field_name:data_user['fullname'], self.login_id_field_name:data_user[self.moodle_id_field_name]})
                            if self.active_field_name!=None:
                                setattr(user_instance, self.active_field_name, True)
                            if 'profileimageurl' in data_user.keys() and data_user['profileimageurl']!='' and data_user['profileimageurl']!=None:
                                photo=self.download_photo(data_user['profileimageurl'])
                                fname=HashManager.getSHA1file(photo)
                                getattr(user_instance, self.photo_field_name).save(f'{fname}.jpg', photo, save=True)
                            user_instance.save()
                            return True, user_instance
            except:
                pass
        return False, None

    def start_session(self, login_id_value, password, permanent=False):
        """ Start session

        Args:
            login_id_value (str): login id value
            password (str): password
            permanent (bool, optional): if True, session will be permanent. Defaults to False.
        Returns:
            tuple:(status (bool), user_insrance (UserObject), token (str), error_message (ErrorMsgType))
        """
        if self.user_model!=None:
            try:
                valid, user_instance=self._auth_with_moodle(login_id_value, password)
                if valid:
                    token=self._generate_token(user_instance, 0 if permanent else self.session_expiration_time)
                    return True, user_instance, token, ErrorManager.get_error_by_code(NO_ERROR)
                if self.user_model.objects.filter(**{self.login_id_field_name:login_id_value}).exists():
                    user_instance=self.user_model.objects.get(**{self.login_id_field_name:login_id_value})
                    if self.active_field_name==None or getattr(user_instance, self.active_field_name):
                        if check_password(password, getattr(user_instance, self.password_field_name)):
                            token=self._generate_token(user_instance, 0 if permanent else self.session_expiration_time)
                            if token!=None:
                                return True, user_instance, token, ErrorManager.get_error_by_code(NO_ERROR)
                            else:
                                return False, None, '', ErrorManager.get_error_by_code(INTERNAL_ERROR)
                        else:
                            return False, None, '', ErrorManager.get_error_by_code(INVALID_CREDENTIALS)
                    else:
                        return False, None, '', ErrorManager.get_error_by_code(INVALID_CREDENTIALS)
                else:
                    return False, None, '', ErrorManager.get_error_by_code(INVALID_CREDENTIALS)
            except:
                return False, None, '', ErrorManager.get_error_by_code(INTERNAL_ERROR)
        else:
            return False, None, '', ErrorManager.get_error_by_code(INTERNAL_ERROR)

    def download_photo(self, url):
        img_temp = tempfile.TemporaryFile(suffix='.jpg')
        r=requests.get(url)
        img_temp.write(r.content)
        img_temp.flush()
        photo=ImageFile(img_temp)
        return photo

    def start_social_session(self, token, origin):
        """ Start session from social network

        Args:
            token (str): token
            origin (str): origin
        Returns:
            tuple:(status (bool), user_insrance (UserObject), token (str), error_message (ErrorMsgType))
        """
        if self.user_model!=None:
            try:
                if origin==self.social_origin_facebook:
                    valid, data = FacebookSession.validate(token)
                    if valid:
                        id=data['id']
                        nombre=data['name']
                        email=data['email']
                        urlfoto=data['picture']['data']['url']
                    else:
                        return False, None, '', ErrorManager.get_error_by_code(INVALID_TOKEN)
                elif origin==self.social_origin_google:
                    valid, data = GoogleSession.validate(token)
                    if valid:
                        id=data['sub']
                        nombre=data['name']
                        email=data['email']
                        urlfoto=data['picture']
                    else:
                        return False, None, '', ErrorManager.get_error_by_code(INVALID_TOKEN)
                else:
                    return False, None, '', ErrorManager.get_error_by_code(INVALID_TOKEN)
                if self.user_model.objects.filter(**{self.social_id_field:id, self.social_origin_field:origin}).exists():
                    user_instance=self.user_model.objects.get(**{self.social_id_field:id, self.social_origin_field:origin})
                    if self.active_field_name==None or getattr(user_instance, self.active_field_name):
                        token=self._generate_token(user_instance, 0)
                        if token!=None:
                            return True, user_instance, token, ErrorManager.get_error_by_code(NO_ERROR)
                        else:
                            return False, None, '0', ErrorManager.get_error_by_code(BAD_GENERATED_TOKEN)
                    else:
                        return False, None, '', ErrorManager.get_error_by_code(INVALID_CREDENTIALS)
                elif self.user_model.objects.filter(**{self.login_id_field_name:email}).exists():
                    user_instance=self.user_model.objects.get(**{self.login_id_field_name:email})
                    if self.active_field_name==None or not getattr(user_instance, self.active_field_name):
                        setattr(user_instance, self.social_id_field, id)
                        setattr(user_instance, self.social_origin_field, origin)
                        if self.active_field_name!=None:
                            setattr(user_instance, self.active_field_name, True)
                        user_instance.save()
                        token=self._generate_token(user_instance, 0)
                        if token!=None:
                            return True, user_instance, token, ErrorManager.get_error_by_code(NO_ERROR)
                        else:
                            return False, None, '1', ErrorManager.get_error_by_code(BAD_GENERATED_TOKEN)
                    else:
                        return False, None, '', ErrorManager.get_error_by_code(SUSPENDED_USER)
                else:
                    user_instance=self.user_model(**{self.social_id_field:id, self.name_field_name:nombre, self.login_id_field_name:email, self.social_origin_field:origin})
                    if self.active_field_name!=None:
                        setattr(user_instance, self.active_field_name, True)
                    photo=self.download_photo(urlfoto)
                    fname=HashManager.getSHA1file(photo)
                    getattr(user_instance, self.photo_field_name).save(f'{fname}.jpg', photo, save=True)
                    user_instance.save()
                    token=self._generate_token(user_instance, 0)
                    if token!=None:
                        return True, user_instance, token, ErrorManager.get_error_by_code(NO_ERROR)
                    else:
                        return False, None, '2', ErrorManager.get_error_by_code(BAD_GENERATED_TOKEN)
            except Exception as e:
                return False, None, '', ErrorManager.get_error_by_code(error_code=INTERNAL_ERROR, custom_message=str(e), custom_description=str(e))
        else:
            return False, None, '', ErrorManager.get_error_by_code(INTERNAL_ERROR)

    def actual_user_attr_getter(self, field_name):
        """ Generate a function that recive info, **kwargs and return the value of field_name of the actual user """
        def actual_user_attr_getter_func(info, model_instance, **kwargs):
            valid, user_instance, error_message=self.validate_access(info.context, 'all')
            sub_attrs=field_name.split('__')
            compare_object=user_instance
            for sub_attr in sub_attrs:
                compare_object=getattr(compare_object, sub_attr)
                if compare_object==None and sub_attr!=sub_attrs[-1]:
                    return None
            return compare_object
        return actual_user_attr_getter_func
    
    def build_access_level_validator(self, model_field='rol', kwargs_field='rol'):
        """ Buuild a validator that validate if a model_instance.model_field is in the actual_user's access level """
        def access_level_validator(info, model_instance, **kwargs):
            valid, user_instance, error_message=self.validate_access(info.context, 'all')
            if valid:
                sub_attrs=model_field.split('__')
                compare_object=model_instance
                for sub_attr in sub_attrs:
                    compare_object=getattr(compare_object, sub_attr)
                    if compare_object==None and sub_attr!=sub_attrs[-1]:
                        return False
                if compare_object in self.group_manager.get_modify_permissions(user_instance) and kwargs.get(kwargs_field, None) in self.group_manager.get_modify_permissions(user_instance):
                    return True
                else:
                    return False
            else:
                return False
        return access_level_validator
        
    def actual_user_comparer(self, actual_user_field, operator, model_field=None, kwargs_key=None, default_value=None):
        """ Build a function that compare the value of actual_user.actual_user_field with the value of model.model_field or kwargs[kwargs_key] or default_value or default_value(info, model_instance, **kwargs) by operator: '=', '!=', '>', '<', '>=', '<=', 'in', 'not in', 'like', 'not like' """
        def actual_user_comparer_func(info, model_instance, **kwargs):
            valid, user_instance, error_message=self.validate_access(info.context, 'all')
            sub_attrs_user=actual_user_field.split('__')
            operator_function=OPERATIONS[operator]
            compare_user_object=user_instance
            for sub_attr_user in sub_attrs_user:
                compare_user_object=getattr(compare_user_object, sub_attr_user)
                if compare_user_object==None and sub_attr_user!=sub_attrs_user[-1]:
                    return False
            user_attr_value = compare_user_object
            if model_field==None and kwargs_key==None:
                if callable(default_value):
                    return operator_function(user_attr_value, default_value(info, model_instance, kwargs))
                else:
                    return operator_function(user_attr_value, default_value)
            if model_instance!=None and model_field!=None:
                if valid:
                    sub_attrs_instance=model_field.split('__')
                    compare_instance_object=model_instance
                    for sub_attr_instance in sub_attrs_instance:
                        compare_instance_object=getattr(compare_instance_object, sub_attr_instance)
                        if compare_instance_object==None and sub_attr_instance!=sub_attrs_instance[-1]:
                            return False
                    return operator_function(user_attr_value, compare_instance_object)
            if kwargs_key!=None and kwargs_key in kwargs.keys():
                if valid:
                    return operator_function(user_attr_value, kwargs[kwargs_key])
            return False
        return actual_user_comparer_func

    