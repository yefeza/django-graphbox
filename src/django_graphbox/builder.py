# graphene imports
import graphene
from graphene_django.types import DjangoObjectType
# error management
from .exceptions import ErrorManager, ErrorMsgType
# global constants
from .constants import *
# build helpers
from .helpers.mutations import *
from .helpers.queries import *
from .helpers.sessions import *

class SchemaBuilder:
    """ Class provides the functionality to build a GraphQL schema with basic operations: field_by_id, list_field, create_field, update_field and delete_field."""

    def __init__(self, session_manager=None):
        """Initialize the schema builder.

        Args:
            session_manager (SessionManager): Session manager to use.
        """
        self._models_config = {}
        self._models_by_op_name = {}
        self._session_manager = session_manager

    def add_model(self, model, exclude_fields=(), pagination_length=0, pagination_style='infinite', external_filters=[], internal_filters=[], filters_opeator=Q.AND, access_group=None, access_by_operation={}, validators_by_operation={}, internal_field_resolvers={}, exclude_fields_by_operation={}, save_as_password=[], callbacks_by_operation={}, custom_attrs_for_type=[], ordering_field='id', **kwargs):
        """Add model for build operations.

        Args:
            model (django.models.Model): Model to add to the schema.
            exclude_fields (tuple or list): Fields to exclude from the model type.
            pagination_length (int): Number of items to return in a paginated response. 0 means no pagination.
            pagination_style (str): Pagination style. Possible values are 'infinite' and 'paginated'.
            external_filters (list): Filters to apply to the model. Each filter is a dictionary with the following keys: 'field_name', 'param_name', 'param_type'. 
            internal_filters (list): Internal filters to apply to the model. Each filter is a dictionary with the following keys: 'field_name', 'resolver_filter', 'on_return_none'. 
            filters_opeator (Q.AND, Q.OR): Operator to use for the filters.
            access_group (str): Access group to use for this model configured in ACCESS_GROUPS of session manager. This will be overriden by the access_by_operation.
            access_by_operation (dict): Dictionary with the operations to use for the access. {'operation': 'access_group', ...}
            validators_by_operation (dict): Dictionary with the validators to use for the access. {'operation': callable(info, model_instance, **kwargs), ...}
            internal_field_resolvers (dict): Dictionary with the internal field value resolvers on create_field and update_field operations
            save_as_password (list): List of fields to save as password with make_password function.
            callbacks_by_operation (dict): Dictionary with the callbacks list to use for the access. {'operation': [callable(info, model_instance, **kwargs)], ...}
            custom_attrs_for_type (list): List of custom attributes to add to the model type. [{'name': 'attr_name', 'value': 'attr_value'}, ...]
            ordering_field (str): Field to use for ordering the list_field operation.
        """
        #get the model name
        model_name = model.__name__
        #crreate the model type
        model_metaclass = type(f"Meta", (), {'model': model, 'exclude_fields': exclude_fields})
        type_attrs={'Meta': model_metaclass}
        for attr in custom_attrs_for_type:
            type_attrs[attr['name']]=attr['value']
        model_type = type(f"{model_name}Type", (DjangoObjectType,), type_attrs)
        #create paginated type
        if pagination_length > 0 and pagination_style == 'paginated':
            paginated_type = type(f"{model_name}PageType", (graphene.ObjectType,), {'items': graphene.List(model_type), 'page': graphene.Int(), 'has_next_page': graphene.Boolean(), 'has_previous_page': graphene.Boolean(), 'total_pages': graphene.Int(), 'total_items': graphene.Int()})
        else:
            paginated_type = None
        #make a new model config
        config = {
            'model': model,
            'name': model_name,
            'type': model_type,
            'pagination_length': pagination_length,
            'pagination_style': pagination_style,
            'paginated_type': paginated_type,
            'external_filters': external_filters,
            'internal_filters': internal_filters,
            'filters_operator': filters_opeator,
            'access_group': access_group,
            'access_by_operation': access_by_operation,
            'validators_by_operation': validators_by_operation,
            'internal_field_resolvers': internal_field_resolvers,
            'exclude_fields_by_operation': exclude_fields_by_operation,
            'save_as_password': save_as_password,
            'callbacks_by_operation': callbacks_by_operation,
            'ordering_field': ordering_field
        }
        self._models_config[model_name]=config

    def build_schema_query(self):
        """ Build query class for the schema.

        Returns:
            graphene.ObjectType: Query class for the schema.
        """
        query_class= type("Query", (graphene.ObjectType,), {})
        for key in self._models_config.keys():
            model_config=self._models_config[key]
            object_name=model_config['name'].lower()
            # build field_by_id query
            field_by_id_resolver_function=build_field_by_id_resolver(self)
            self._models_by_op_name[object_name]=model_config
            setattr(query_class, object_name, graphene.Field(model_config['type'], id=graphene.ID(required=True)))
            setattr(query_class, f'resolve_{object_name}', field_by_id_resolver_function)
            # build list_field query
            field_list_resolver_function=build_field_list_resolver(self)
            self._models_by_op_name['all' + object_name]=model_config
            return_object=get_return_object(model_config)
            setattr(query_class, f"all_{object_name}", return_object)
            setattr(query_class, f'resolve_all_{object_name}',field_list_resolver_function)
        return query_class
    
    def build_schema_mutation(self):
        """Build mutations class for the schema. 
        
        Returns:
            graphene.ObjectType: Mutations class for the schema.
        """
        mutation_class= type("Mutation", (), {})
        for key in self._models_config.keys():
            model_config=self._models_config[key]
            # create the create mutation
            mutate_create_function=build_mutate_for_create(self)
            # get fields to ignore on arguments
            fields_to_ignore=get_fields_to_ignore(model_config, 'create_field')
            # build argumants class
            arguments_create=create_arguments_class(model_config['model'], fields_to_ignore)
            create_mutation=type("Create"+model_config['name'], (graphene.Mutation,), {"estado":graphene.Boolean(),model_config['name'].lower(): graphene.Field(model_config['type']), "error":graphene.Field(ErrorMsgType), 'Arguments': arguments_create, 'mutate': mutate_create_function})
            setattr(mutation_class, f"create_{model_config['name'].lower()}", create_mutation.Field())
            self._models_by_op_name['create' + model_config['name'].lower()]=model_config
            # create the update mutation
            mutate_update_function=build_mutate_for_update(self)
            # get fields to omit
            fields_to_ignore=get_fields_to_ignore(model_config, 'update_field')
            # build argumants class
            arguments_update=update_arguments_class(model_config['model'], fields_to_ignore, model_config.get('save_as_password'))
            update_mutation=type("Update"+model_config['name'], (graphene.Mutation,), {"estado":graphene.Boolean(),model_config['name'].lower(): graphene.Field(model_config['type']), "error":graphene.Field(ErrorMsgType), 'Arguments': arguments_update, 'mutate': mutate_update_function})
            setattr(mutation_class, f"update_{model_config['name'].lower()}", update_mutation.Field())
            self._models_by_op_name['update' + model_config['name'].lower()]=model_config
            # create the delete mutation
            mutate_delete_function=build_mutate_for_delete(self)
            # build argumants class
            delete_arguments=delete_arguments_class()
            delete_mutation=type("Delete"+model_config['name'], (graphene.Mutation,), {"estado":graphene.Boolean(), "error":graphene.Field(ErrorMsgType), 'Arguments': delete_arguments, 'mutate': mutate_delete_function})
            setattr(mutation_class, f"delete_{model_config['name'].lower()}", delete_mutation.Field())
            self._models_by_op_name['delete' + model_config['name'].lower()]=model_config
        return mutation_class

    def build_session_schema(self):
        """ Build the session mutations and queries for the schema.
            The operations are:
                - login Mutation
                - social_login Mutation (if the social login is configured)
                - actual_user Query

        Returns:
            tuple: (session_query_class, session_mutation_class)
        """
        if self._session_manager!=None:
            if self._session_manager.user_model.__name__ in self._models_config.keys():
                config_login_model=self._models_config[self._session_manager.user_model.__name__]
            else:
                #get the model name
                model_name = self._session_manager.user_model.__name__
                #crreate the model type
                model_metaclass = type(f"Meta", (), {'model': self._session_manager.user_model, 'exclude_fields': (self._session_manager.password_field_name,)})
                model_type = type(f"{model_name}Type", (DjangoObjectType,), {'Meta': model_metaclass})
                config_login_model = {
                    'model': self._session_manager.user_model,
                    'name': model_name,
                    'type': model_type,
                    'pagination_length': 0,
                    'filters': {},
                    'filters_operator': Q.AND,
                    'access_group': None,
                    'access_by_operation': {}
                }
                self._models_config[model_name]=config_login_model
            #build Login Mutation
            mutation_class= type("Mutation", (), {})
            arguments_class= type("Arguments", (), {'permanent':graphene.Boolean(required=True)})
            setattr(arguments_class, self._session_manager.login_id_field_name, graphene.String(required=True))
            setattr(arguments_class, self._session_manager.password_field_name, graphene.String(required=True))
            login_mutate_function=build_mutate_for_login(self)
            login_mutation=type("Login", (graphene.Mutation,), {'estado': graphene.Boolean(), config_login_model['name'].lower(): graphene.Field(config_login_model['type']), 'token':graphene.String(), 'error': graphene.Field(ErrorMsgType), 'Arguments': arguments_class, 'mutate': login_mutate_function})
            setattr(mutation_class, "login", login_mutation.Field())
            self._models_by_op_name['login']=config_login_model
            # build Social Login Mutation
            if self._session_manager.use_social_session:
                arguments_class= type("Arguments", (), {'token':graphene.String(required=True), 'origin':graphene.String(required=True)})
                social_login_mutate_function=build_mutate_for_social_login(self)
                social_login_mutation=type("SocialLogin", (graphene.Mutation,), {'estado': graphene.Boolean(), config_login_model['name'].lower(): graphene.Field(config_login_model['type']), 'token':graphene.String(), 'error': graphene.Field(ErrorMsgType), 'Arguments': arguments_class, 'mutate': social_login_mutate_function})
                setattr(mutation_class, "social_login", social_login_mutation.Field())
            # build actual_user query
            query_class= type("Query", (graphene.ObjectType,), {})
            actual_user_function=build_actual_user_resolver(self)
            setattr(query_class, "actual_user", graphene.Field(config_login_model['type']))
            setattr(query_class, "resolve_actual_user", actual_user_function)
            self._models_by_op_name['actualuser']=config_login_model
            return query_class, mutation_class
        else:
            assert False, "Session Manager not defined"