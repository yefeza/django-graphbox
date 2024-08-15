# About Django GraphBox

Django GraphBox is a package for easy building GraphQL APIs with Django. This
package is based on Graphene and Graphene-Django.

It provides a SchemaBuilder that can be used to build a GraphQL schema from
Django models. It also provides a SessionManager that can be used to manage
access to the GraphQL API.

The basic idea of this package is to provide a simple way to build a GraphQL API
with Django without the need to write a lot of code. The SchemaBuilder can be
used to build a GraphQL schema from Django models in a few lines of code. The
SessionManager can be used to manage access to the GraphQL API in a few lines of
code.

SchemaBuilder is designed to create the basic CRUD operations for a model. It
can be used to create a GraphQL schema with the basic CRUD operations for a
model. It also provides a way to configure the fields that will be used on the
schema. The SessionManager is designed to manage access to the GraphQL API. It
can be used to manage access to the GraphQL API with a user model. It also
provides a way to configure the groups and permissions that will be used to
manage access to the GraphQL API.

The operations that can be created with the SchemaBuilder are:

- create_field (Mutation)
- update_field (Mutation)
- delete_field (Mutation)
- get_field (Query) this operation will be called with the name of the model,
  for example, if the model is called MyModel then the operation will be called
  my_model and the arguments will be id.
- all_field (Query) this operation will be called with the name of the model,
  for example, if the model is called MyModel then the operation will be called
  all_my_model and the arguments will be filters, page, and others depending on
  the configuration when the model was added to the SchemaBuilder.

When the SessionManager is used, the operations related to authentication are:

- login (Mutation)
- social_login (Mutation)
- actual_user (Query)

This package don't limit to use this basic operations. Custom operations can be
defined on classic style of Graphene and Graphene-Django and finally can be
merged on the main schema as described on the Quickstart section of this
documentation at 4. Create a main schema in a new file called schema.py on
myproject folder. This file can be used to merge all queries and mutations from
all apps builded with django_graphbox or just add your own queries and
mutations.

# Installation

> ```bash
> $ pip install django-graphbox
> ```

# Quickstart

Use this guide to get started with the GraphBox.

1.  Create a new Django project.

    > ```bash
    > $ django-admin startproject myproject
    > $ cd myproject
    > $ python manage.py startapp myapp
    > ```

2.  Add django_graphbox to the INSTALLED_APPS on settings.py file.

    > ```python3
    > INSTALLED_APPS = [
    >     ...
    >     'django_graphbox',
    >     ...
    > ]
    > ```

3.  Define your Django models in the myapp app.

    > ```python3
    > from django.db import models
    >
    > class MyModel(models.Model):
    >     ...
    > ```
    >
    > ```bash
    > $ python manage.py makemigrations myapp
    > $ python manage.py migrate
    > ```

4.  Configure and Build your GraphQL schema with
    django_graphbox.builder.SchemaBuilder on a new file called schema.py on the
    myapp app.

    > ```python3
    > from django_graphbox.builder import SchemaBuilder
    > from myapp.models import MyModel
    >
    > builder = SchemaBuilder()
    > builder.add_model(MyModel)
    > query_class = builder.build_schema_query()
    > mutation_class = builder.build_schema_mutation()
    > ```

5.  Create a main schema in a new file called schema.py on myproject folder.
    This file can be used to merge all queries and mutations from all apps
    builded with django_graphbox or just add your own queries and mutations.

    > ```python3
    > import graphene
    > from myapp.schema import query_class, mutation_class
    >
    > class Query(query_class, graphene.ObjectType):
    >     pass
    >
    > class Mutation(mutation_class, graphene.ObjectType):
    >     pass
    >
    > schema = graphene.Schema(query=Query, mutation=Mutation)
    > ```

6.  Add the schema on urls.py file.

    > ```python3
    > from django.urls import path
    > from graphene_file_upload.django import FileUploadGraphQLView
    > from django.views.decorators.csrf import csrf_exempt
    > from .schema import schema
    >
    > urlpatterns = [
    >     path('graphql/', csrf_exempt(FileUploadGraphQLView.as_view(graphiql=True, schema=schema))),
    > ]
    > ```

7.  Run your project.

    > ```bash
    > $ python manage.py runserver
    > ```

# Basic Authentication

Django GraphBox implements a SessionManager that can be used to manage access to
the GraphQL API. This Manager is based on JWT authentication, so you have to
send on Bearer format the token in the Authorization header.

Follow the steps below to create a new user and Manage the access to the GraphQL
API.

1.  Create your User model.

    > ```python3
    > from django.models import Model
    >
    > class User(Model):
    >     custom_uname = models.CharField(max_length=100)
    >     custom_pwd = models.CharField(max_length=100)
    >     custom_active = models.BooleanField(default=True)
    >     role = models.CharField(max_length=100)
    > ```
    >
    > Note that you can define your fields as you want, and you will be able to
    > configure this fields in the SessionManager.

2.  Configure groups of users based on roles:

    > ```python3
    > ACCESS_GROUPS = {
    >     "GROUP_LEVEL_1": ["RULE_LEVEL1"],
    >     "GROUP_LEVEL_2": ["RULE_LEVEL1", "RULE_LEVEL_2",],
    >     "GROUP_LEVEL_3": ["RULE_LEVEL1" ,"RULE_LEVEL_2", "RULE_LEVEL_3",],
    > }
    > ```
    >
    > This groups can be interpreted as: If an operation is configured for allow
    > to GROUP_LEVEL_2 then the user will be able to create a field only if he
    > has the role RULE_LEVEL_1 or RULE_LEVEL_2.

3.  Create a new instance of the SessionManager on your schema.py file on the
    myapp app and configure the user model.

    > ```python3
    > from django_graphbox.session import Manager as SessionManager
    > from myapp.models import User
    > from django.conf import settings
    >
    > session_manager = SessionManager(User)
    > # You can change the names of default fields like this:
    > session_manager.config_user_model(active_field_name='custom_active', login_id_field_name='custom_uname', rol_field_name='role')
    > # You can change the name of the session key and jwt configuration like this:
    > session_manager.config_session_jwt(persistent_tokens=True, session_key='public-schema', security_key=settings.SECRET_KEY)
    > # You can change the groups and permissions like this:
    > session_manager.config_access_groups(ACCESS_GROUPS)
    > # You can configure Captcha on the session operations like this:
    > session_manager.config_captcha(use_captcha=True, captcha_style='google_recaptcha_v3', recaptcha_site_key=settings.RECAPTCHA_SITE_KEY, recaptcha_secret_key=settings.RECAPTCHA_SECRET_KEY, max_login_attempts=5, max_captcha_by_user=5, expiration_minutes=5, captcha_length=6)
    > ```

4.  Configure and Build your GraphQL schema with
    django_graphbox.builder.SchemaBuilder on the file called schema.py on the
    myapp app.

    > ```python3
    > from django_graphbox.builder import SchemaBuilder
    > from myapp.models import MyModel
    >
    > # Add the SessionManager to the SchemaBuilder
    > builder = SchemaBuilder(session_manager=session_manager)
    > # Build your operations
    > builder.add_model(MyModel, access_group="GROUP_LEVEL_2") # This operation will be available only for users with the permission ROLE_LEVEL_1 or ROLE_LEVEL_2
    > builder.add_model(
    >     User,
    >     exclude_fields=('custom_pwd',), # Exclude this field on the builded ModelType
    >     save_as_password=['custom_pwd',], # On create and update this field will be saved as a password
    >     access_group="GROUP_LEVEL_2",
    >     access_by_operation={'delete_field': 'GROUP_LEVEL_1'}
    >     ) # This operation will be available only for users with the permission ROLE_LEVEL_1 or ROLE_LEVEL_2 except delete_field operation only for users with the permission ROLE_LEVEL_1.
    > query_class = builder.build_schema_query()
    > mutation_class = builder.build_schema_mutation()
    > # Build your session operations
    > session_query, session_mutation = builder.build_session_schema()
    > ```

5.  Create a main schema in a new file called schema.py on myproject folder.
    This file can be used to merge all queries and mutations from all apps
    builded with django_graphbox or just add your own queries and mutations.

    > ```python3
    > import graphene
    > from myapp.schema import query_class, mutation_class, session_query, session_mutation
    >
    > class Query(query_class, session_query, graphene.ObjectType):
    >     pass
    >
    > class Mutation(mutation_class, session_mutation, graphene.ObjectType):
    >     pass
    >
    > schema = graphene.Schema(query=Query, mutation=Mutation)
    > ```

6.  Add the schema on urls.py file.

    > ```python3
    > from django.urls import path
    > from graphene_file_upload.django import FileUploadGraphQLView
    > from django.views.decorators.csrf import csrf_exempt
    > from .schema import schema
    >
    > urlpatterns = [
    >     path('graphql/', csrf_exempt(FileUploadGraphQLView.as_view(graphiql=True, schema=schema))),
    > ]
    > ```

7.  Run the server and try to access the GraphQL API. Session operations will be
    available called actualUser query and login mutation. Additionally you can
    see the operations will require a valid access token and will validate the
    user role and permissions as you configured.

# Custom filters, validators and internal resolvers

Django GraphBox Builder allows you to add custom filters and validators to the
GraphQL schema. This example assumes that you have two models called User and
Favorite.

> ```python3
> class User(Model):
>     custom_uname = models.CharField(max_length=100)
>     custom_pwd = models.CharField(max_length=100)
>     custom_active = models.BooleanField(default=True)
>     role = models.CharField(max_length=100)
>
> class Favorite(Model):
>     book_name = models.CharField(max_length=100)
>     book_author = models.CharField(max_length=100)
>     book_year = models.IntegerField()
>     user = models.ForeignKey(User, on_delete=models.CASCADE)
> ```

1.  You can add external filters for the Favorite query. External filters are
    parameters that will be provided by the client and will be used to filter
    the query. The filters are added to the external_filters dictionary on the
    add_model method like this:

    > ```python3
    > builder.add_model(
    >     Favorite,
    >     external_filters={
    >         {
    >             "field_name": "book_name", # The field name on the Favorite model
    >             "param_name": "book_name", # The parameter name on the query
    >             "param_type": graphene.String(required=True), # The parameter graphene type
    >         }
    >     }
    > )
    > ```

2.  You can add internal filters for the Favorite query. Internal filters are
    callables that will be resolved on the query execution with the parameters
    of the query resolver.

    > ```python3
    > def filter_resolver(info, **kwargs):
    >     # Write your custom filter based on the info, and kwargs parameters and return the value expected for field_name.
    >     logged, actual_user = session_manager.validate_access(info.context, "GROUP_LEVEL_1") # You can use the session_manager methods to validate the get data of the actual user
    >     return actual_user.id
    >
    > builder.add_model(
    >     Favorite,
    >     internal_filters={
    >         "field_name": "user__id", # The field name on the Favorite model
    >         "resolver_filter": filter_resolver, # The callable resolver that will be executed on the query execution
    >         "on_return_none": "skip", # If the function returns None, the filter will be skipped. If you want apply the filter like user__id__is_null=True, you can set this parameter to "set__isnull".
    >     }
    > )
    > ```
    >
    > This will build the query allFavorite filtered by the actual user.

3.  Build operations with custom validators by operation for a customizable
    workflow. The validators callables need receive info, model_instance,
    \*\*kwargs and must return a boolean.

    > ```python3
    > def custom_validator_1(info, model_instance, **kwargs):
    >     # Write your custom validator based on the info, model_instance and kwargs parameters and return a boolean.
    >     logged, actual_user = session_manager.validate_access(info.context, "GROUP_LEVEL_1") # You can use the session_manager methods to validate the get data of the actual user
    >     return actual_user.id == model_instance.user.id
    >
    > def custom_validator_2(info, model_instance, **kwargs):
    >     # Write your custom validator based on the info, model_instance and kwargs parameters and return a boolean.
    >     return model_instance.book_year > 2000
    >
    > builder.add_model(
    >     Favorite,
    >     validators_by_operation={
    >         'create_field': {
    >             'validators':[
    >                 custom_validator_1, # This function will validate if the actual user is the owner of the Favorite instance on the create operation
    >                 custom_validator_2, # This function will validate if the book_year is greater than 2000 on the create operation
    >                 { # You can use a dict to create a complex validator
    >                     'validators':[
    >                         custom_validator_1, # This function will validate if the actual user is the owner of the Favorite instance on the create operation
    >                         custom_validator_2, # This function will validate if the book_year is greater than 2000 on the create operation
    >                     ],
    >                     'connector': 'AND', # The connector between the validators. If you want to use OR, you can set this parameter to 'OR'.
    >             }
    >             ],
    >             'connector': 'OR', # The connector between the validators. If you want to use AND, you can set this parameter to 'AND'.
    >         },
    >     }
    > )
    >
    > The validators are evaluated recursively, this allows you to create complex validators replacing the callable function with other dict with the same structure.
    > ```

4.  Build operations with internal resolvers for some fields of the model. For
    example to set the actual user as the owner of the Favorite. The resolver
    callables need receive info, model_instance, \*\*kwargs and must return the
    value expected for the field.

    > ```python3
    > builder.add_model(
    >     Favorite,
    >     internal_field_resolvers={
    >         'create_field': {
    >             'user': session_manager.actual_user_attr_getter(field_name='id'), # This function of session_manager will return a function that return the id of the actual user
    >         },
    >         'update_field': {
    >             'user': session_manager.actual_user_attr_getter(field_name='id'), # This function of session_manager will return a function that return the id of the actual user
    >         },
    >     }
    > )
    > ```
    >
    > Note that the ForeignKey fields need return the id of the related model.

5.  Build operations based on modify_permissions. For this example we will
    configure the User operations for allow create, update and delete to the
    actual user only if this has permission.

    > ```python3
    > builder.add_model(
    >     User,
    >     validators_by_operation={
    >         'create_field': {
    >             'validators':(
    >                 session_manager.build_access_level_validator(model_field='role'), # This function of session_manager will return a function that compare the role of the actual user with the role of the User instance on the create operation
    >             ),
    >             'connector': 'OR', # The connector between the validators. If you want to use AND, you can set this parameter to 'AND'.
    >         },
    >         'update_field': {
    >             'validators':(
    >                 session_manager.build_access_level_validator(model_field='role'), # This function of session_manager will return a function that compare the role of the actual user with the role of the User instance on the update operation
    >             ),
    >             'connector': 'OR', # The connector between the validators. If you want to use AND, you can set this parameter to 'AND'.
    >         },
    >         'delete_field': {
    >             'validators':(
    >                 session_manager.build_access_level_validator(model_field='role'), # This function of session_manager will return a function that compare the role of the actual user with the role of the User instance on the delete operation
    >             ),
    >             'connector': 'OR', # The connector between the validators. If you want to use AND, you can set this parameter to 'AND'.
    >         },
    >     }
    > )
    >
    > SessionManager.build_access_level_validator(model_field='role') will return a function that will validate if the user_instance.role exists on the list of MODIFY_PERMISSIONS[actual_user.role].
    > ```

# Social Login

This package has support for social login with Google and Facebook.

## Google

1.  Create a project on
    [Google Cloud Platform](https://console.cloud.google.com/).

2.  Create a OAuth 2.0 client ID on the Credentials section of the Google Cloud
    Platform.

3.  Add the client ID and client secret on the settings.py file.

```python3
    GOOGLE_CLIENT_ID='YOUR_CLIENT_ID'
```

4. Setup SessionManager to use social login:

```python3
    session_manager = SessionManager(
        Usuario,
        use_social_session=True, # This will enable the social login
        session_key='public-schema', # This is the key of the session
        active_field_name='activo', # This is the name of the active field of the model
        login_id_field_name='email', # This is the name of the field that will be used to login
        rol_field_name='tipo', # This is the name of the field that will be used to set the role of the user
        name_field_name='nombres', # This is the name of the field that will be used to set the name of the user (this will be set from response of the social login)
        photo_field_name='foto', # This is the name of the field that will be used to set the photo of the user (this will be set from response of the social login)
        social_id_field='social_id', # This is the name of the field that will be used to set the social id of the user (this will be set from response of the social login)
        social_origin_field='social_origin', # This is the name of the field that will be used to set the social origin of the user (this will be send on social login mutation to identify the social login origin and can be 'FACEBOOK' or 'GOOGLE')
        security_key=settings.SECRET_KEY, # Key used to generate the token
        groups=PUBLIC_ACCESS_GROUPS, # Explained on the previous section
        modify_permissions=PUBLIC_MODIFY_PERMISSIONS # Explained on the previous section
        )
```

5. Use the session_manager to create the schema builder:

```python3
    builder = SchemaBuilder(session_manager) # Explained on the previous section
```

## Facebook

1.  Create an app on [Facebook Developers](https://developers.facebook.com/).

2.  Configure the app to use Facebook Login.

3.  Add FACEBOOK_APP_ID in settings.py file:

```python3
    FACEBOOK_APP_ID='YOUR_APP_ID'
```

4. Setup SessionManager like the Google example. The social authentication will
   be the same, and the only difference is the social_origin_field that will be
   'FACEBOOK' when the socialLogin mutation is called.

# Extra Features

Django Graphbox has some extra features that can be used, but the documentation
is not complete yet. If you want to use this features, you can see the code of
the package to know how to use it or see the API Reference.

Some of the extra features are:

- Pagination for queries (infinitely scrolling and paginated)
- Moodle authentication (login with moodle credentials and get the user data
  from moodle)
- Internal filters (filters that can be used to filter the data of the query
  based on a callable resolver)
- Validators by operation (validators that can be used to validate the data of
  the mutation based on a callable resolver)
- Internal field resolvers (resolvers that can be used to resolve the data of
  the field based on a callable resolver)
- Callbacks by operation (callbacks that can be used to execute a callable
  resolver after the mutation is executed)
- Automatic integration with
  [Django Auditor Logs](https://pypi.org/project/django-auditor-logs/) (A
  package that can be used to log the data changes on the models, maintained by
  the same author of this package)

# Release Notes

> - Version 1.0.0 to 1.1.5 was a package developed for a specific project, and
>   the code was not published on GitHub. The code was refactored and published
>   on GitHub on version 1.2.0.
> - Version 1.2.3 add support to set custom attributes on the model Type and set
>   custom ordering field for the queries.
> - Version 1.2.4 Fix custom attributes on the model Type.
> - Version 1.2.5 Add support to select the operations to build for the model.
>   You can select between field_by_id, list_field, create_field, update_field
>   and delete_field operations. By default all operations are selected.
> - Version 1.2.7 Add support for Google Login using OAuth 2.0 with OpenID
>   Connect.
> - Version 1.2.8 Optimize optional dependencies.
> - Version 1.2.9 Fix bug on Django auditor logs integration.
> - Version 1.2.10 Fix ordering field and callbacks on delete operation.
> - Version 1.3 Add captcha controls in session operations and persistent tokens
> - Version 1.4.1 Fix bugs
> - Version 1.4.2 Add support for callable security key on session manager
