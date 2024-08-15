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
import google.oauth2.credentials
from google.auth.transport.requests import AuthorizedSession

# facebook imports
import facebook

# files manage
from django.core.files.images import ImageFile
from django.core.files.temp import tempfile

# Hash manager
from .hasher import HashManager

# Logging
import logging

# Models
from django_graphbox.models import FailedLoginAttempt, JsonWebToken, LoginCaptcha

# Json
import json

# requests
import requests

# random string
import string
import random

# Moodle
try:
    from moodle import Moodle
except:
    pass


class GroupManager:
    """Manager for allow access to users by groups."""

    _groups = {}
    _user_model = None
    _role_field_name = "rol"

    def __init__(self, user_model, role_field_name, groups={}, **kwargs):
        """Initialize the GroupManager.

        Args:
            user_model (class): The user model class.
            role_field_name (str): The name of the field that contains the user rol.
            groups (dict): The groups and their user rol list. {'group_name': ['rol_1', 'rol_2', ...], ...}
        """
        self._user_model = user_model
        self._role_field_name = role_field_name
        self._groups = groups

    def add_group(self, group_name, access_list):
        """Add a new group to the manager."""
        self._groups[group_name] = access_list

    def validar_acesso(self, user_instance, group_name):
        """Validate if a user_instance is on a group_name."""
        if self._user_model != None and isinstance(user_instance, self._user_model):
            if hasattr(user_instance, self._role_field_name):
                if (
                    group_name == "all"
                    or getattr(user_instance, self._role_field_name)
                    in self._groups[group_name]
                ):
                    return True
                return False


class GoogleSession:
    client_id = getattr(settings, "GOOGLE_CLIENT_ID", None)

    @classmethod
    def validate(cls, token):
        try:
            credentials = google.oauth2.credentials.Credentials(token)
            authed_session = AuthorizedSession(credentials)
            open_id_configuration = requests.get(
                "https://accounts.google.com/.well-known/openid-configuration"
            ).json()
            userinfo_endpoint = open_id_configuration["userinfo_endpoint"]
            # Make an authenticated API request with OPENID scope.
            response = authed_session.get(userinfo_endpoint, params={"alt": "json"})
            info = response.json()
            return True, info
        except:
            try:
                info = id_token.verify_oauth2_token(token, grq.Request(), cls.client_id)
                return True, info
            except:
                data = []
                return False, data


class FacebookSession:
    app_id = getattr(settings, "FACEBOOK_APP_ID", None)

    @classmethod
    def validate(cls, token):
        try:
            graph = facebook.GraphAPI(access_token=token, version="3.1")
            info = graph.get_object("me", fields="id,email,name,picture")
            return True, info
        except:
            data = []
            return False, data


class Manager:
    def __init__(
        self,
        user_model,
        **kwargs,
    ):
        """Session Manager for a user_model

        Args:
            user_model (django.models.Model): User model
            **kwargs (dict): Deprecated arguments
        """
        if user_model == None:
            raise Exception("user_model must be defined")
        self.user_model = user_model
        if len(kwargs) > 0:
            logging.warning(
                "WARNING: kwargs is deprecated, use config_user_model, config_social_session, config_session_jwt, config_access_groups and config_moodle instead"
            )
        # Configuracion de campos del modelo de usuario
        self.config_user_model(**kwargs)
        # Configuracion de campos del modelo de usuario para login social
        self.config_social_session(**kwargs)
        # Configuracion de la sesión JWT
        self.config_session_jwt(**kwargs)
        # Configuracion de grupos de acceso
        self.config_access_groups(**kwargs)
        # Configuracion de autenticacion con moodle
        self.config_moodle(**kwargs)
        # Configuracion de captcha
        self.config_captcha(**kwargs)

    def config_user_model(
        self,
        role_field_name="role",
        login_id_field_name="uname",
        password_field_name="password",
        active_field_name=None,
        name_field_name="name",
        photo_field_name="photo",
        **kwargs,
    ):
        """Configure user model

        Args:
            role_field_name (str, optional): Field name of user model for access level control. Defaults to 'role'.
            login_id_field_name (str, optional): Field name of unique field used for authentication. Defaults to 'uname'.
            password_field_name (str, optional): Field name of password field used for authentication. Defaults to 'password'.
            active_field_name (str, optional): Field name for boolean field name for validation active user. Defaults to None for not validation.
        """
        # Validar tipos
        if type(role_field_name) != str:
            raise Exception("role_field_name must be string")
        if type(login_id_field_name) != str:
            raise Exception("login_id_field_name must be string")
        if type(password_field_name) != str:
            raise Exception("password_field_name must be string")
        if active_field_name != None and type(active_field_name) != str:
            raise Exception("active_field_name must be string")
        if type(name_field_name) != str:
            raise Exception("name_field_name must be string")
        if type(photo_field_name) != str:
            raise Exception("photo_field_name must be string")
        # Configuracion de campos del modelo de usuario
        self.role_field_name = role_field_name
        if kwargs.get("rol_field_name") != None:
            self.role_field_name = kwargs.get("rol_field_name")
            logging.warning(
                "WARNING: rol_field_name is deprecated, use role_field_name instead"
            )
        self.login_id_field_name = login_id_field_name
        self.password_field_name = password_field_name
        self.active_field_name = active_field_name
        self.name_field_name = name_field_name
        self.photo_field_name = photo_field_name

    def config_social_session(
        self,
        use_social_session=False,
        social_id_field=None,
        social_origin_field=None,
        **kwargs,
    ):
        """Configure social session

        Args:
            social_id_field (str, optional): Field name of social id field used for authentication. Defaults to 'social_id'.
            social_origin_field (str, optional): Field name of social origin field used for authentication. Defaults to 'social_origin'.
        """
        # Validar tipos
        if use_social_session and type(use_social_session) != bool:
            raise Exception("use_social_session must be boolean")
        if social_id_field and type(social_id_field) != str:
            raise Exception("social_id_field must be string")
        if social_origin_field and type(social_origin_field) != str:
            raise Exception("social_origin_field must be string")
        self.use_social_session = use_social_session
        if self.use_social_session:
            if self.name_field_name == None or self.photo_field_name == None:
                raise Exception("name_field_name and photo_field_name must be defined")
        self.social_id_field = social_id_field
        self.social_origin_field = social_origin_field
        self.social_origin_facebook = "FACEBOOK"
        self.social_origin_google = "GOOGLE"

    def config_access_groups(
        self,
        groups={},
        **kwargs,
    ):
        """Set access groups

        Args:
            groups (dict): Predefined access groups {"group_name":["rol_1", "rol_2", "rol_3"]}. Defaults to {}.
        """
        # Validar tipos
        if type(groups) != dict:
            raise Exception("groups must be dict")
        self.group_manager = GroupManager(self.user_model, self.role_field_name, groups)

    def config_session_jwt(
        self,
        session_key=None,
        session_expiration_time=12,
        security_key=None,
        persistent_tokens=False,
        **kwargs,
    ):
        """Configure session jwt

        Args:
            session_key (str, optional): Session key to identify the session. Defaults to None for only one schema.
            session_expiration_time (int, optional): Time in hours to set expiration time on jwt when not permanent session. Defaults to 12.
            security_key (str, optional): Secret used as secret for sign on jwt. Defaults to None for use django.conf.settings.SECRET_KEY.
            persistent_tokens (bool, optional): If True, tokens will be persistent. Defaults to False.
        """
        # Validar tipos
        if session_key != None and type(session_key) != str:
            raise Exception("session_key must be string")
        if type(session_expiration_time) != int:
            raise Exception("session_expiration_time must be int")
        if (
            security_key != None
            and type(security_key) != str
            and not callable(security_key)
        ):
            raise Exception("security_key must be string or function")
        if type(persistent_tokens) != bool:
            raise Exception("persistent_tokens must be boolean")
        # Configuracion de la sesión JWT
        self.session_key = session_key
        self.session_expiration_time = session_expiration_time
        if security_key != None:
            self._security_key = security_key
        else:
            self._security_key = settings.SECRET_KEY
        self.persistent_tokens = persistent_tokens

    def config_moodle(
        self,
        moodle_urls=[],
        moodle_auth_field_name="username",
        moodle_id_field_name="email",
        **kwargs,
    ):
        """Configure moodle

        Args:
            moodle_urls (list or function, optional): List of moodle urls or function that return a list of moodle urls. Defaults to [].
            moodle_auth_field_name (str, optional): Field name of moodle user model for authentication. Defaults to 'username'.
            moodle_id_field_name (str, optional): Field name of moodle user model for identification. Defaults to 'email'.
        """
        # Validar tipos
        if type(moodle_urls) != list and not callable(moodle_urls):
            raise Exception("moodle_urls must be list or function")
        if type(moodle_auth_field_name) != str:
            raise Exception("moodle_auth_field_name must be string")
        if type(moodle_id_field_name) != str:
            raise Exception("moodle_id_field_name must be string")
        if self.name_field_name == None:
            raise Exception("name_field_name must be defined")
        # Configuracion de autenticacion con moodle
        self.moodle_urls = moodle_urls
        self.moodle_auth_field_name = moodle_auth_field_name
        self.moodle_id_field_name = moodle_id_field_name

    def config_captcha(
        self,
        use_captcha=False,
        captcha_style="classic",
        recaptcha_secret_key=None,
        recaptcha_site_key=None,
        max_login_attempts=1,
        max_captcha_by_user=6,
        expiration_minutes=1,
        captcha_length=6,
        **kwargs,
    ):
        """Configure recaptcha

        Args:
            use_captcha (bool, optional): If True, captcha will be used. Defaults to False.
            captcha_style (str, optional): Style of captcha. Defaults to 'classic'.
            recaptcha_secret_key (str, optional): Secret key for recaptcha. Defaults to None.
            recaptcha_site_key (str, optional): Site key for recaptcha. Defaults to None.
            max_login_attempts (int, optional): Max attempts for failed login before captcha required. Defaults to 1.

            max_captcha_by_user (int, optional): Max captcha generated in 1 hour for user. Defaults to 3.
            expiration_minutes (int, optional): Expiration time in minutes for captcha. Defaults to 1.
        """
        # Validar tipos
        if type(use_captcha) != bool:
            raise Exception("use_captcha must be boolean")
        if type(captcha_style) != str and not callable(captcha_style):
            raise Exception("captcha_style must be string or function")
        if (
            recaptcha_secret_key != None
            and type(recaptcha_secret_key) != str
            and not callable(recaptcha_secret_key)
        ):
            raise Exception("recaptcha_secret_key must be string or function")
        if (
            recaptcha_site_key != None
            and type(recaptcha_site_key) != str
            and not callable(recaptcha_site_key)
        ):
            raise Exception("recaptcha_site_key must be string or function")
        if type(max_login_attempts) != int:
            raise Exception("max_login_attempts must be int")
        if type(max_captcha_by_user) != int:
            raise Exception("max_captcha_by_user must be int")
        if type(expiration_minutes) != int:
            raise Exception("expiration_minutes must be int")
        if type(captcha_length) != int:
            raise Exception("captcha_length must be int")
        self.use_captcha = use_captcha
        self.captcha_style = captcha_style
        if captcha_style == "google_recaptcha_v3":
            if recaptcha_secret_key == None:
                raise Exception("recaptcha_secret_key must be defined")
            if recaptcha_site_key == None:
                raise Exception("recaptcha_site_key must be defined")
        self.recaptcha_secret_key = recaptcha_secret_key
        self.recaptcha_site_key = recaptcha_site_key
        self.max_login_attempts = max_login_attempts
        self.max_captcha_by_user = max_captcha_by_user
        self.expiration_minutes = expiration_minutes
        self.captcha_length = captcha_length

    def config_middleware_path(self, middleware_path):
        self.middleware_path = middleware_path

    def preprocess_user_data(self, request):
        if "Authorization" in request.headers:
            token = request.headers["Authorization"]
            token = token[7 : len(token)]
            try:
                if callable(self._security_key):
                    security_key = self._security_key(token=token)
                else:
                    security_key = self._security_key
                payload = jwt.decode(token, security_key, algorithms=["HS256"])
                if (
                    not self.persistent_tokens
                    or JsonWebToken.objects.filter(
                        token=token,
                        active=True,
                        session_key=self.session_key,
                        user_id=payload["u_id"],
                    ).exists()
                ):
                    if (
                        self.session_key == None
                        or self.session_key == payload["session_key"]
                    ):
                        if self.user_model.objects.filter(id=payload["u_id"]).exists():
                            user_instance = self.user_model.objects.get(
                                id=payload["u_id"]
                            )
                            if self.active_field_name == None or getattr(
                                user_instance, self.active_field_name
                            ):
                                # import django_auditor_logs if exists
                                if "django_auditor_logs" in settings.INSTALLED_APPS:
                                    try:
                                        from django_auditor_logs.metadata import (
                                            MetadataManager,
                                        )

                                        user_metadata = {}
                                        for field in user_instance._meta.get_fields():
                                            try:
                                                if not field.is_relation:
                                                    if (
                                                        field.name
                                                        != self.password_field_name
                                                    ):
                                                        user_metadata[field.name] = str(
                                                            getattr(
                                                                user_instance,
                                                                field.name,
                                                            )
                                                        )
                                                else:
                                                    user_metadata[
                                                        field.name + "_id"
                                                    ] = str(
                                                        getattr(
                                                            user_instance,
                                                            field.name,
                                                        ).id
                                                    )
                                            except:
                                                pass
                                        MetadataManager.set_user_metadata(user_metadata)
                                    except Exception as e:
                                        print(e)
                                return (
                                    True,
                                    user_instance,
                                    ErrorManager.get_error_by_code(NO_ERROR),
                                )
                            else:
                                return (
                                    False,
                                    None,
                                    ErrorManager.get_error_by_code(ACCESS_DENIED),
                                )
                        else:
                            return (
                                False,
                                None,
                                ErrorManager.get_error_by_code(INVALID_CREDENTIALS),
                            )
                    else:
                        return (
                            False,
                            None,
                            ErrorManager.get_error_by_code(INVALID_TOKEN),
                        )
                else:
                    return False, None, ErrorManager.get_error_by_code(INVALID_TOKEN)
            except:
                return False, None, ErrorManager.get_error_by_code(INVALID_TOKEN)
        else:
            return False, None, ErrorManager.get_error_by_code(INVALID_TOKEN)

    def validate_access(self, request, group_name):
        """Validate access

        Args:
            request (django.http.request.HttpRequest): request to validate Authorization header as Bearer token
            group_name (str): group name to validate
        Returns:
            tuple:(status (bool), user_instance (UserObject))
        """
        if group_name == "open" or group_name == None:
            return True, None, ErrorManager.get_error_by_code(NO_ERROR)
        if hasattr(request, "graphbox_auth_info"):
            if request.graphbox_auth_info["valid"]:
                user_instance = request.graphbox_auth_info["user_instance"]
                estado = self.group_manager.validar_acesso(user_instance, group_name)
                if estado:
                    return True, user_instance, ErrorManager.get_error_by_code(NO_ERROR)
                else:
                    return False, None, ErrorManager.get_error_by_code(ACCESS_DENIED)
            else:
                return False, None, request.graphbox_auth_info["session_error"]
        if "Authorization" in request.headers:
            token = request.headers["Authorization"]
            token = token[7 : len(token)]
            try:
                if callable(self._security_key):
                    security_key = self._security_key(token=token)
                else:
                    security_key = self._security_key
                payload = jwt.decode(token, security_key, algorithms=["HS256"])
                if (
                    not self.persistent_tokens
                    or JsonWebToken.objects.filter(
                        token=token,
                        active=True,
                        session_key=self.session_key,
                        user_id=payload["u_id"],
                    ).exists()
                ):
                    if (
                        self.session_key == None
                        or self.session_key == payload["session_key"]
                    ):
                        if self.user_model.objects.filter(id=payload["u_id"]).exists():
                            user_instance = self.user_model.objects.get(
                                id=payload["u_id"]
                            )
                            if self.group_manager.validar_acesso(
                                user_instance, group_name
                            ):
                                if self.active_field_name == None or getattr(
                                    user_instance, self.active_field_name
                                ):
                                    # import django_auditor_logs if exists
                                    if "django_auditor_logs" in settings.INSTALLED_APPS:
                                        try:
                                            from django_auditor_logs.metadata import (
                                                MetadataManager,
                                            )

                                            user_metadata = {}
                                            for (
                                                field
                                            ) in user_instance._meta.get_fields():
                                                try:
                                                    if not field.is_relation:
                                                        if (
                                                            field.name
                                                            != self.password_field_name
                                                        ):
                                                            user_metadata[
                                                                field.name
                                                            ] = str(
                                                                getattr(
                                                                    user_instance,
                                                                    field.name,
                                                                )
                                                            )
                                                    else:
                                                        user_metadata[
                                                            field.name + "_id"
                                                        ] = str(
                                                            getattr(
                                                                user_instance,
                                                                field.name,
                                                            ).id
                                                        )
                                                except:
                                                    pass
                                            MetadataManager.set_user_metadata(
                                                user_metadata
                                            )
                                        except Exception as e:
                                            print(e)
                                    return (
                                        True,
                                        user_instance,
                                        ErrorManager.get_error_by_code(NO_ERROR),
                                    )
                                else:
                                    return (
                                        False,
                                        None,
                                        ErrorManager.get_error_by_code(ACCESS_DENIED),
                                    )
                            else:
                                return (
                                    False,
                                    None,
                                    ErrorManager.get_error_by_code(ACCESS_DENIED),
                                )
                        else:
                            return (
                                False,
                                None,
                                ErrorManager.get_error_by_code(INVALID_CREDENTIALS),
                            )
                    else:
                        return (
                            False,
                            None,
                            ErrorManager.get_error_by_code(INVALID_TOKEN),
                        )
                else:
                    return False, None, ErrorManager.get_error_by_code(INVALID_TOKEN)
            except:
                return False, None, ErrorManager.get_error_by_code(INVALID_TOKEN)
        else:
            return False, None, ErrorManager.get_error_by_code(INVALID_TOKEN)

    def _get_request_metadata(self):
        request_metadata = None
        try:
            from django_auditor_logs.metadata import MetadataManager

            request_metadata = json.dumps(MetadataManager.get_request_metadata())
        except:
            logging.info(
                "SUGGESTION: install django_auditor_logs if you want to save request metadata on persistent tokens"
            )
        return request_metadata

    def _generate_token(self, user_instance, expiration_time=0):
        """Generate jwt for user_instance

        Args:
            user_instance (user_model.__class__): user instance to generate token
            expiration_time (int, optional): expiration time in hours. Defaults to 0 for no expiration.
        Returns:
            str: generated token
        """
        if self.user_model != None and isinstance(user_instance, self.user_model):
            session_id = str(uuid4())
            payload = {
                "session_id": session_id,
                "u_id": user_instance.id,
            }
            if self.session_key != None:
                payload["session_key"] = self.session_key
            if expiration_time > 0:
                payload["exp"] = tz.localtime() + datetime.timedelta(
                    hours=expiration_time
                )
            if callable(self._security_key):
                security_key = self._security_key(user_instance=user_instance)
            else:
                security_key = self._security_key
            token = jwt.encode(payload, security_key, algorithm="HS256")
            if self.persistent_tokens:
                request_metadata = self._get_request_metadata()
                persistent_data = JsonWebToken(
                    token=token,
                    request_metadata=request_metadata,
                    session_key=self.session_key,
                    user_id=user_instance.id,
                )
                persistent_data.save()
            return token
        return None

    def _auth_with_moodle(self, login_id, password):
        """Validate user with moodle

        Args:
            login_id (str): login id
            password (str): password

        Returns:
            tuple:(status (bool), user_instance (UserObject))
        """
        final_moodle_urls = self.moodle_urls
        if type(self.moodle_urls) == list:
            final_moodle_urls = self.moodle_urls
        elif callable(self.moodle_urls):
            final_moodle_urls = self.moodle_urls()
        for moodle_data in final_moodle_urls:
            try:
                response = requests.post(
                    moodle_data["url"] + "/login/token.php",
                    data={
                        self.moodle_auth_field_name: login_id,
                        "password": password,
                        "service": "moodle_mobile_app",
                    },
                )
                if response.status_code == 200:
                    # validate only if token exists
                    json_response = response.json()
                    if "token" in json_response.keys():
                        moodle = Moodle(
                            moodle_data["url"] + "/webservice/rest/server.php",
                            moodle_data["token"],
                        )
                        # get user info
                        data_user = moodle(
                            "core_user_get_users_by_field",
                            field=self.moodle_auth_field_name,
                            values=[login_id],
                        )
                        if len(data_user) > 0:
                            data_user = data_user[0]
                            if self.user_model.objects.filter(
                                **{
                                    self.login_id_field_name: data_user[
                                        self.moodle_id_field_name
                                    ]
                                }
                            ).exists():
                                user_instance = self.user_model.objects.get(
                                    **{
                                        self.login_id_field_name: data_user[
                                            self.moodle_id_field_name
                                        ]
                                    }
                                )
                                if self.active_field_name == None or getattr(
                                    user_instance, self.active_field_name
                                ):
                                    return True, user_instance
                                else:
                                    self._save_failed_login_attempt(
                                        login_id, password, user_instance.id
                                    )
                                    return False, None
                            else:
                                user_instance = self.user_model(
                                    **{
                                        self.name_field_name: data_user["fullname"],
                                        self.login_id_field_name: data_user[
                                            self.moodle_id_field_name
                                        ],
                                    }
                                )
                                if self.active_field_name != None:
                                    setattr(user_instance, self.active_field_name, True)
                                if (
                                    self.photo_field_name != None
                                    and "profileimageurl" in data_user.keys()
                                    and data_user["profileimageurl"] != ""
                                    and data_user["profileimageurl"] != None
                                ):
                                    try:
                                        photo = self.download_photo(
                                            data_user["profileimageurl"]
                                        )
                                        fname = HashManager.getSHA1file(photo)
                                        getattr(
                                            user_instance, self.photo_field_name
                                        ).save(f"{fname}.jpg", photo, save=False)
                                    except:
                                        pass
                                user_instance.save()
                                return True, user_instance
                    else:
                        self._save_failed_login_attempt(login_id, password)
            except:
                pass
        return False, None

    def _auth_native(self, login_id_value, password):
        if self.user_model.objects.filter(
            **{self.login_id_field_name: login_id_value}
        ).exists():
            user_instance = self.user_model.objects.get(
                **{self.login_id_field_name: login_id_value}
            )
            if self.active_field_name == None or getattr(
                user_instance, self.active_field_name
            ):
                if getattr(
                    user_instance, self.password_field_name
                ) != None and check_password(
                    password, getattr(user_instance, self.password_field_name)
                ):
                    return True, user_instance
                else:
                    self._save_failed_login_attempt(
                        login_id_value, password, user_instance.id
                    )
                    return False, user_instance
            else:
                self._save_failed_login_attempt(
                    login_id_value, password, user_instance.id
                )
                return False, user_instance
        else:
            self._save_failed_login_attempt(login_id_value, password)
            return False, None

    def _save_failed_login_attempt(self, login_id_value, password, user_id=None):
        """Save failed login attempt

        Args:
            login_id_value (str): login id value
            password (str): password
        """
        request_metadata = self._get_request_metadata()
        failed_login_attempt = FailedLoginAttempt(
            username=login_id_value,
            password=password,
            request_metadata=request_metadata,
            session_key=self.session_key,
            user_id=user_id,
        )
        failed_login_attempt.save()

    def _is_captcha_required(self, user_instance=None):
        """Validate if captcha is required

        Args:
            user_instance (UserObject): user instance
        Returns:
            bool: True if captcha is required
        """
        if self.use_captcha:
            before_one_hour = tz.localtime() - datetime.timedelta(hours=1)
            if user_instance != None:
                failed_login_attempts = FailedLoginAttempt.objects.filter(
                    user_id=user_instance.id,
                    session_key=self.session_key,
                    timestamp__gte=before_one_hour,
                ).count()
            else:
                failed_login_attempts = FailedLoginAttempt.objects.filter(
                    session_key=self.session_key,
                    timestamp__gte=before_one_hour,
                ).count()
            if failed_login_attempts >= self.max_login_attempts:
                return True
        return False

    def _update_captcha_status(self):
        """Update captcha status"""
        expire_captcha = tz.localtime() - datetime.timedelta(
            minutes=self.expiration_minutes
        )
        LoginCaptcha.objects.filter(
            creation_time__lte=expire_captcha,
            session_key=self.session_key,
        ).update(active=False)

    def _validate_classic_captcha(self, user_instance, captcha_id, captcha_value):
        """Validate classic captcha

        Args:
            user_instance (UserObject): user instance
            captcha_id (str): captcha id
            captcha_value (str): captcha value
        Returns:
            bool: True if captcha is valid
        """
        self._update_captcha_status()
        if captcha_id != None and captcha_value != None:
            if user_instance != None:
                return (
                    LoginCaptcha.objects.all()
                    .filter(
                        captcha_id=captcha_id,
                        captcha_value=captcha_value,
                        active=True,
                        session_key=self.session_key,
                        user_id=user_instance.id,
                    )
                    .exists()
                )
            else:
                return (
                    LoginCaptcha.objects.all()
                    .filter(
                        captcha_id=captcha_id,
                        captcha_value=captcha_value,
                        active=True,
                        session_key=self.session_key,
                        user_id__isnull=True,
                    )
                    .exists()
                )
        else:
            return False

    def _validate_google_recaptcha_v3(self, recaptcha_token):
        """Validate google recaptcha v3

        Args:
            recaptcha_token (str): recaptcha token
        Returns:
            bool: True if captcha is valid
        """
        try:
            url = "https://www.google.com/recaptcha/api/siteverify"
            data = {"secret": self.recaptcha_secret_key, "response": recaptcha_token}
            response = requests.post(url, data=data)
            if response.status_code == 200:
                data = response.json()
                return data["success"]
            return False
        except:
            return False

    def _validate_captcha(
        self,
        user_instance=None,
        captcha_id=None,
        captcha_value=None,
        recaptcha_token=None,
    ):
        """Validate captcha

        Args:
            captcha_id (str, optional): captcha id. Defaults to None.
            captcha_value (str, optional): captcha value. Defaults to None.
            recaptcha_token (str, optional): recaptcha token. Defaults to None.
        Returns:
            bool: True if captcha is valid
        """
        if self.use_captcha:
            if self._is_captcha_required(user_instance=user_instance):
                if callable(self.captcha_style):
                    captcha_style = self.captcha_style()
                else:
                    captcha_style = self.captcha_style
                if captcha_style == "classic":
                    return self._validate_classic_captcha(
                        user_instance, captcha_id, captcha_value
                    )
                elif captcha_style == "google_recaptcha_v3":
                    return self._validate_google_recaptcha_v3(recaptcha_token)
                else:
                    raise Exception("captcha_style is not valid")
        return True

    def start_session(
        self,
        login_id_value,
        password,
        permanent=False,
        captcha_id=None,
        captcha_value=None,
        recaptcha_token=None,
    ):
        """Start session

        Args:
            login_id_value (str): login id value
            password (str): password
            permanent (bool, optional): if True, session will be permanent. Defaults to False.
        Returns:
            tuple:(status (bool), user_instance (UserObject), token (str), error_message (ErrorMsgType), captcha_required=bool)
        """
        if self.user_model != None:
            try:
                valid, user_instance = self._auth_with_moodle(login_id_value, password)
                if not valid:
                    valid, user_instance = self._auth_native(login_id_value, password)
                if self._validate_captcha(
                    user_instance=user_instance,
                    captcha_id=captcha_id,
                    captcha_value=captcha_value,
                    recaptcha_token=recaptcha_token,
                ):
                    if valid:
                        token = self._generate_token(
                            user_instance,
                            0 if permanent else self.session_expiration_time,
                        )
                        return (
                            True,
                            user_instance,
                            token,
                            ErrorManager.get_error_by_code(NO_ERROR),
                            False,
                        )
                    else:
                        captcha_required = self._is_captcha_required(
                            user_instance=user_instance
                        )
                        return (
                            False,
                            None,
                            "",
                            ErrorManager.get_error_by_code(INVALID_CREDENTIALS),
                            captcha_required,
                        )
                else:
                    return (
                        False,
                        None,
                        "",
                        ErrorManager.get_error_by_code(INVALID_CAPTCHA),
                        True,
                    )
            except:
                return (
                    False,
                    None,
                    "",
                    ErrorManager.get_error_by_code(INTERNAL_ERROR),
                    False,
                )
        else:
            return (
                False,
                None,
                "",
                ErrorManager.get_error_by_code(INTERNAL_ERROR),
                False,
            )

    def _random_captcha_value(self):
        """Generate random captcha value

        Returns:
            str: random captcha value
        """
        return "".join(
            random.choice(string.ascii_uppercase + string.digits)
            for _ in range(self.captcha_length)
        )

    def generate_classic_captcha(self, login_id_value):
        """Generate classic captcha

        Args:
            user_instance (UserObject): user instance
        Returns:
            tuple:(captcha_id (str), captcha_value (str))
        """
        if self.use_captcha:
            user_instance = self.user_model.objects.filter(
                **{self.login_id_field_name: login_id_value}
            ).first()
            if self._is_captcha_required(user_instance=user_instance):
                self._update_captcha_status()
                before_one_hour = tz.localtime() - datetime.timedelta(hours=1)
                if user_instance != None:
                    cantidad_captchas = LoginCaptcha.objects.filter(
                        user_id=user_instance.id,
                        session_key=self.session_key,
                        creation_time__gte=before_one_hour,
                    ).count()
                else:
                    cantidad_captchas = LoginCaptcha.objects.filter(
                        session_key=self.session_key,
                        creation_time__gte=before_one_hour,
                    ).count()
                if cantidad_captchas < self.max_captcha_by_user:
                    captcha_id = str(uuid4())
                    captcha_value = self._random_captcha_value()
                    user_id = None
                    if user_instance != None:
                        user_id = user_instance.id
                    login_captcha = LoginCaptcha(
                        captcha_id=captcha_id,
                        captcha_value=captcha_value,
                        session_key=self.session_key,
                        user_id=user_id,
                    )
                    login_captcha.save()
                    return captcha_id
        return None

    def download_photo(self, url):
        img_temp = tempfile.TemporaryFile(suffix=".jpg")
        r = requests.get(url)
        img_temp.write(r.content)
        img_temp.flush()
        photo = ImageFile(img_temp)
        return photo

    def start_social_session(self, token, origin):
        """Start session from social network

        Args:
            token (str): token
            origin (str): origin
        Returns:
            tuple:(status (bool), user_instance (UserObject), token (str), error_message (ErrorMsgType))
        """
        if self.user_model != None:
            try:
                if origin == self.social_origin_facebook:
                    valid, data = FacebookSession.validate(token)
                    if valid:
                        id = data["id"]
                        nombre = data["name"]
                        email = data["email"]
                        urlfoto = data["picture"]["data"]["url"]
                    else:
                        return (
                            False,
                            None,
                            "",
                            ErrorManager.get_error_by_code(INVALID_TOKEN),
                        )
                elif origin == self.social_origin_google:
                    valid, data = GoogleSession.validate(token)
                    if valid:
                        id = data["sub"]
                        nombre = data["name"]
                        email = data["email"]
                        urlfoto = data["picture"]
                    else:
                        return (
                            False,
                            None,
                            "",
                            ErrorManager.get_error_by_code(INVALID_TOKEN),
                        )
                else:
                    return (
                        False,
                        None,
                        "",
                        ErrorManager.get_error_by_code(INVALID_TOKEN),
                    )
                if self.user_model.objects.filter(
                    **{self.social_id_field: id, self.social_origin_field: origin}
                ).exists():
                    user_instance = self.user_model.objects.get(
                        **{self.social_id_field: id, self.social_origin_field: origin}
                    )
                    if self.active_field_name == None or getattr(
                        user_instance, self.active_field_name
                    ):
                        token = self._generate_token(user_instance, 0)
                        if token != None:
                            return (
                                True,
                                user_instance,
                                token,
                                ErrorManager.get_error_by_code(NO_ERROR),
                            )
                        else:
                            return (
                                False,
                                None,
                                "0",
                                ErrorManager.get_error_by_code(BAD_GENERATED_TOKEN),
                            )
                    else:
                        return (
                            False,
                            None,
                            "",
                            ErrorManager.get_error_by_code(INVALID_CREDENTIALS),
                        )
                elif self.user_model.objects.filter(
                    **{self.login_id_field_name: email}
                ).exists():
                    user_instance = self.user_model.objects.get(
                        **{self.login_id_field_name: email}
                    )
                    if self.active_field_name == None or not getattr(
                        user_instance, self.active_field_name
                    ):
                        setattr(user_instance, self.social_id_field, id)
                        setattr(user_instance, self.social_origin_field, origin)
                        if self.active_field_name != None:
                            setattr(user_instance, self.active_field_name, True)
                        user_instance.save()
                        token = self._generate_token(user_instance, 0)
                        if token != None:
                            return (
                                True,
                                user_instance,
                                token,
                                ErrorManager.get_error_by_code(NO_ERROR),
                            )
                        else:
                            return (
                                False,
                                None,
                                "1",
                                ErrorManager.get_error_by_code(BAD_GENERATED_TOKEN),
                            )
                    else:
                        return (
                            False,
                            None,
                            "",
                            ErrorManager.get_error_by_code(SUSPENDED_USER),
                        )
                else:
                    user_instance = self.user_model(
                        **{
                            self.social_id_field: id,
                            self.name_field_name: nombre,
                            self.login_id_field_name: email,
                            self.social_origin_field: origin,
                        }
                    )
                    if self.active_field_name != None:
                        setattr(user_instance, self.active_field_name, True)
                    photo = self.download_photo(urlfoto)
                    fname = HashManager.getSHA1file(photo)
                    getattr(user_instance, self.photo_field_name).save(
                        f"{fname}.jpg", photo, save=True
                    )
                    user_instance.save()
                    token = self._generate_token(user_instance, 0)
                    if token != None:
                        return (
                            True,
                            user_instance,
                            token,
                            ErrorManager.get_error_by_code(NO_ERROR),
                        )
                    else:
                        return (
                            False,
                            None,
                            "2",
                            ErrorManager.get_error_by_code(BAD_GENERATED_TOKEN),
                        )
            except Exception as e:
                return (
                    False,
                    None,
                    "",
                    ErrorManager.get_error_by_code(
                        error_code=INTERNAL_ERROR,
                        custom_message=str(e),
                        custom_description=str(e),
                    ),
                )
        else:
            return False, None, "", ErrorManager.get_error_by_code(INTERNAL_ERROR)

    def actual_user_attr_getter(self, field_name):
        """Generate a function that recive info, model_instance, **kwargs and return the value of field_name of the actual user"""

        def actual_user_attr_getter_func(info, model_instance, **kwargs):
            valid, user_instance, error_message = self.validate_access(
                info.context, "all"
            )
            sub_attrs = field_name.split("__")
            compare_object = user_instance
            for sub_attr in sub_attrs:
                compare_object = getattr(compare_object, sub_attr)
                if compare_object == None and sub_attr != sub_attrs[-1]:
                    return None
            return compare_object

        return actual_user_attr_getter_func
