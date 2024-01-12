# graphene imports
import graphene

# error management
from django_graphbox.exceptions import ErrorMsgType

# login mutate function builder


def build_mutate_for_login(self):
    def login_mutate_function(parent, info, **kwargs):
        config = self._models_by_op_name["login"]
        login_id_value = kwargs.get(self._session_manager.login_id_field_name)
        password_value = kwargs.get(self._session_manager.password_field_name)
        permanent = kwargs.get("permanent")
        captcha_id = kwargs.get("captcha_id")
        captcha_value = kwargs.get("captcha_value")
        recaptcha_token = kwargs.get("recaptcha_token")
        (
            valid,
            user_instance,
            token,
            error,
            captcha_required,
        ) = self._session_manager.start_session(
            login_id_value,
            password_value,
            permanent=permanent,
            captcha_id=captcha_id,
            captcha_value=captcha_value,
            recaptcha_token=recaptcha_token,
        )
        return_object = type(
            info.return_type.name,
            (graphene.ObjectType,),
            {
                "estado": graphene.Boolean(),
                "token": graphene.String(),
                user_instance.__class__.__name__.lower(): graphene.Field(
                    config["type"]
                ),
                "error": graphene.Field(ErrorMsgType),
                "captcha_required": graphene.Boolean(),
            },
        )
        return return_object(
            **{
                "estado": valid,
                "token": token,
                user_instance.__class__.__name__.lower(): user_instance,
                "error": error,
                "captcha_required": captcha_required,
            }
        )

    return login_mutate_function


# social login mutate function builder
def build_mutate_for_social_login(self):
    def social_login_mutate_function(parent, info, **kwargs):
        config = self._models_by_op_name["login"]
        token = kwargs.get("token")
        origin = kwargs.get("origin")
        valid, user_instance, token, error = self._session_manager.start_social_session(
            token, origin
        )
        return_object = type(
            info.return_type.name,
            (graphene.ObjectType,),
            {
                "estado": graphene.Boolean(),
                "token": graphene.String(),
                user_instance.__class__.__name__.lower(): graphene.Field(
                    config["type"]
                ),
                "error": graphene.Field(ErrorMsgType),
            },
        )
        return return_object(
            **{
                "estado": valid,
                "token": token,
                user_instance.__class__.__name__.lower(): user_instance,
                "error": error,
            }
        )

    return social_login_mutate_function


# actual user query resolver builder


def build_actual_user_resolver(self):
    def actual_user_function(parent, info, **kwargs):
        valid, user_instance, error = self._session_manager.validate_access(
            info.context, "all"
        )
        return user_instance

    return actual_user_function


# captcha query resolver builder


def build_captcha_resolver(self):
    def captcha_function(parent, info, **kwargs):
        user_login_id = kwargs.get("user_id")
        captcha_id = self._session_manager.generate_classic_captcha(user_login_id)
        return captcha_id

    return captcha_function
