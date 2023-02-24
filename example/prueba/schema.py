# django_graphbox imports.
from django_graphbox.builder import SchemaBuilder
from django_graphbox.session import Manager as SessionManager
import graphene
# models imports.
from .models import *
# settings imports.
from django.conf import settings

# Create session manager
session_manager = SessionManager(
    CustomUser, 
    active_field_name='is_active', 
    rol_field_name='rol',
    login_id_field_name='email',
    password_field_name='password',
    name_field_name='name',
    photo_field_name='foto',
    social_id_field='social_id',
    social_origin_field='social_origin',
    use_social_session=True,
    session_key='main-schema', 
    security_key=settings.SECRET_KEY, 
    groups=settings.ACCESS_GROUPS, 
    modify_permissions=settings.MODIFY_PERMISSIONS
    )
# Create your schema here.
builder=SchemaBuilder(session_manager=session_manager)
# Add models to schema
builder.add_model(
    CustomUser,
    exclude_fields=('password', ),
    save_as_password=['password'],
    access_group=settings.GROUP_RESPONSABLE,
)
builder.add_model(
    RelatedModel,
    access_group=settings.GROUP_RESPONSABLE,
)
builder.add_model(
    Prueba,
    access_group=settings.GROUP_AUXILIAR,
)
# build session schema
session_query, session_mutation = builder.build_session_schema()
# build the schema queries and mutations
query=builder.build_schema_query()
mutation=builder.build_schema_mutation()