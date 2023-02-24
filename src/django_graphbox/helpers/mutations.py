# graphene imports
import graphene
# global constants
from django_graphbox.constants import *
# error management
from django_graphbox.exceptions import ErrorManager, ErrorMsgType
# hasher import
from django_graphbox.hasher import HashManager
# shared helpers
from django_graphbox.helpers.shared import *
# django imports
from django.core.files import File
from django.core.files.images import ImageFile
from django.contrib.auth.hashers import make_password
# pillow import
from PIL import Image
# json 
import json

# Arguments class Builders

def create_arguments_class(model, fields_to_ignore=[]):
    """Create graphene arguments class for create_field operation

    Args:
        model (object): Django model class to create arguments class for.
        fields_to_ignore (list): list of fields resolved internally that don't need to be on arguments class.
    Returns:
        class: Arguments class

    The returned class has this structure:
    Example::
        class Arguments:
            model_field_name_str = graphene.String(required=True) # required=True if field is not null
            model_field_name_2_bool = graphene.Boolean(required=True) # model_field will be converted to equivalent graphene type
    """
    class Arguments:
        pass
    exclude_fields = ['id', 'created_at', 'updated_at'] + fields_to_ignore
    for field in model._meta.fields:
        if field.name not in exclude_fields:
            field_type=field.get_internal_type()
            if field_type in MODEL_FIELD_TO_GRAPHENE_TYPE.keys():
                argument_type=MODEL_FIELD_TO_GRAPHENE_TYPE[field_type]
                required=True
                if field.null:
                    required=False
                setattr(Arguments, field.name.lower(), argument_type(required=required))
    return Arguments

def update_arguments_class(model, fields_to_ignore=[], fields_as_password=[]):
    """ Create graphene arguments class for update_field operation 
    
    Args:
        model (object): Django model class to create arguments class for.
        fields_to_ignore (list): list of fields resolved internally that don't need to be on arguments class.
        fields_as_password (list): list of fields that should be treated as password fields.
    Returns:
        class: Arguments class
    """
    class Arguments:
        pass
    exclude_fields = ['created_at', 'updated_at'] + fields_to_ignore
    for field in model._meta.fields:
        if field.name not in exclude_fields:
            field_type=field.get_internal_type()
            if field_type!='ManyToManyField':
                argument_type=MODEL_FIELD_TO_GRAPHENE_TYPE[field_type]
                required=True
                if field.null or field_type in ['ImageField', 'FileField'] or field.name in fields_as_password:
                    required=False
                setattr(Arguments, field.name.lower(), argument_type(required=required))
    return Arguments

def delete_arguments_class():
    """ Create graphene arguments class for delete_field operation 
    
    Returns:
        class: Arguments class
    The returned class has this structure:
    Example::
        class Arguments:
            id = graphene.ID(required=True)
    """
    class Arguments:
        id=graphene.ID(required=True)
    return Arguments

# mutate function builders

def build_mutate_for_create(self):
    """ Build mutate function for create_field operation
        Args:
            self (object): SchemaBuilder object
    """
    def mutate_create_function(parent, info, **kwargs):
        operation_name=info.operation.selection_set.selections[0].name.value.lower()
        config=self._models_by_op_name[operation_name]
        # get access group for validate access
        access_group=get_access_group('create_field', config)
        if self._session_manager!=None:
            valid, actual_user_instance, session_error=self._session_manager.validate_access(info.context, access_group)
        else:
            valid=True
        model=config.get('model')
        return_object=type(info.return_type.name, (graphene.ObjectType,), {'estado':graphene.Boolean(), model.__name__.lower():graphene.Field(config['type']),'error':graphene.Field(ErrorMsgType)})
        if valid:
            try:
                instance=model()
                # get internal resolvers
                internal_field_resolvers=config.get('internal_field_resolvers')
                if 'create_field' in internal_field_resolvers.keys():
                    fields_to_resolve=internal_field_resolvers.get('create_field')
                    kwargs.update(fields_to_resolve)
                for key, value in kwargs.items():
                    field_type=instance._meta.get_field(key).__class__.__name__
                    if callable(value):
                        value=value(info, instance, **kwargs)
                    if value!=None:
                        if field_type=='ForeignKey':
                            foreign_model=instance._meta.get_field(key).related_model
                            value=foreign_model.objects.get(id=value)
                            setattr(instance, key, value)
                        elif field_type=='FileField':
                            file=File(value)
                            extension=file.name.split('.')[-1]
                            sha1_file=HashManager.getSHA1file(file)
                            getattr(instance, key).save(f'{sha1_file}.{extension}', file, save=False)
                        elif field_type=='ImageField':
                            #test if is a valid image
                            Image.open(value)
                            file=ImageFile(value)
                            extension=file.name.split('.')[-1]
                            sha1_file=HashManager.getSHA1file(file)
                            getattr(instance, key).save(f'{sha1_file}.{extension}', file, save=False)
                        elif key in config.get('save_as_password'):
                            value=make_password(value)
                            setattr(instance, key, value)
                        else:
                            if model._meta.get_field(key).choices!=None and len(model._meta.get_field(key).choices)>0:
                                choices=model._meta.get_field(key).choices
                                valid_options=[c[0] for c in choices]
                                if value not in valid_options:
                                    raise Exception(f'{value} no es una opción válida para {key}')
                            setattr(instance, key, value)
                # evaluate validators
                valid_operation=True
                if 'create_field' in config['validators_by_operation']:
                    valid_operation=evaluate_result(config['validators_by_operation']['create_field'], info, instance, **kwargs)
                if valid_operation:
                    instance.save()
                    callbacks=config.get('callbacks_by_operation').get('create_field')
                    if callbacks is not None:
                        for callback in callbacks:
                            if callable(callback):
                                callback(info, instance, **kwargs)
                    return return_object(**{'estado':True, model.__name__.lower():instance, 'error':ErrorManager.get_error_by_code(NO_ERROR)})
                else:
                    return return_object(**{'estado':False, 'error':ErrorManager.get_error_by_code(INSUFFICIENT_PERMISSIONS)})
            except Exception as e:
                return return_object(**{'estado':False, 'error':ErrorManager.get_error_by_code(error_code=UNKNOWN_ERROR, custom_message="Error Inesperado", custom_description=str(e))})
        else:
            return return_object(**{'estado':False, 'error':session_error})
    return mutate_create_function

def build_mutate_for_update(self):
    def mutate_update_function(parent, info, **kwargs):
        operation_name=info.operation.selection_set.selections[0].name.value.lower()
        config=self._models_by_op_name[operation_name]
        # get access group for validate access
        access_group=get_access_group('update_field', config)
        if self._session_manager!=None:
            valid, actual_user_instance, session_error=self._session_manager.validate_access(info.context, access_group)
        else:
            valid=True
        model=config.get('model')
        return_object=type(info.return_type.name, (graphene.ObjectType,), {'estado':graphene.Boolean(), model.__name__.lower():graphene.Field(config['type']),'error':graphene.Field(ErrorMsgType)})
        if valid:
            try:
                if model.objects.filter(id=kwargs.get('id')).exists():
                    instance=model.objects.get(id=kwargs.get('id'))
                    valid_operation=True
                    if 'update_field' in config['validators_by_operation']:
                        valid_operation=evaluate_result(config['validators_by_operation']['update_field'], info, instance, **kwargs)
                    if valid_operation:
                        # get internal resolvers
                        internal_field_resolvers=config.get('internal_field_resolvers')
                        if 'update_field' in internal_field_resolvers.keys():
                            fields_to_resolve=internal_field_resolvers.get('update_field')
                            kwargs.update(fields_to_resolve)
                        for key, value in kwargs.items():
                            if key!='id':
                                field_type=instance._meta.get_field(key).__class__.__name__
                                if callable(value):
                                    value=value(info, instance, **kwargs)
                                if value!=None:
                                    if field_type=='ForeignKey':
                                        foreign_model=instance._meta.get_field(key).related_model
                                        value=foreign_model.objects.get(id=value)
                                        setattr(instance, key, value)
                                    elif field_type=='FileField':
                                        file=File(value)
                                        extension=file.name.split('.')[-1]
                                        sha1_file=HashManager.getSHA1file(file)
                                        getattr(instance, key).save(f'{sha1_file}.{extension}', file, save=False)
                                    elif field_type=='ImageField':
                                        #test if is a valid image
                                        Image.open(value)
                                        file=ImageFile(value)
                                        extension=file.name.split('.')[-1]
                                        sha1_file=HashManager.getSHA1file(file)
                                        getattr(instance, key).save(f'{sha1_file}.{extension}', file, save=False)
                                    elif key in config.get('save_as_password'):
                                        value=make_password(value)
                                        setattr(instance, key, value)
                                    else:
                                        if model._meta.get_field(key).choices!=None and len(model._meta.get_field(key).choices)>0:
                                            choices=model._meta.get_field(key).choices
                                            valid_options=[c[0] for c in choices]
                                            if value not in valid_options:
                                                raise Exception(f'{value} no es una opción válida para {key}')
                                        setattr(instance, key, value)
                        instance.save()
                        callbacks=config.get('callbacks_by_operation').get('update_field')
                        if callbacks is not None:
                            for callback in callbacks:
                                if callable(callback):
                                    callback(info, instance, **kwargs)
                        return return_object(**{'estado':True, model.__name__.lower():instance, 'error':ErrorManager.get_error_by_code(NO_ERROR)})
                    else:
                        return return_object(**{'estado':False, 'error':ErrorManager.get_error_by_code(INSUFFICIENT_PERMISSIONS)})
                else:
                    return return_object(**{'estado':False, 'error':ErrorManager.get_error_by_code(INSTANCE_NOT_FOUND)})
            except Exception as e:
                return return_object(**{'estado':False, 'error':ErrorManager.get_error_by_code(error_code=UNKNOWN_ERROR,custom_message="Error Inesperado", custom_description=str(e))})
        else:
            return return_object(**{'estado':False, 'error':session_error})
    return mutate_update_function

def build_mutate_for_delete(self):
    def mutate_delete_function(parent, info, **kwargs):
        operation_name=info.operation.selection_set.selections[0].name.value.lower()
        config=self._models_by_op_name[operation_name]
        # get access group for validate access
        access_group=get_access_group('delete_field', config)
        if self._session_manager!=None:
            valid, actual_user_instance, session_error=self._session_manager.validate_access(info.context, access_group)
        else:
            valid=True
        model=config.get('model')
        return_object=type(info.return_type.name, (graphene.ObjectType,), {'estado':graphene.Boolean(), 'error':graphene.Field(ErrorMsgType)})
        if valid:
            try:
                if model.objects.filter(id=kwargs.get('id')).exists():
                    instance=model.objects.get(id=kwargs.get('id'))
                    valid_operation=True
                    if 'delete_field' in config['validators_by_operation']:
                        valid_operation=evaluate_result(config['validators_by_operation']['delete_field'], info, instance, **kwargs)
                    if valid_operation:
                        callbacks=config.get('callbacks_by_operation').get('delete_field')
                        if callbacks is not None:
                            for callback in callbacks:
                                if callable(callback):
                                    callback(info, instance, **kwargs)
                        instance.delete()
                        return return_object(**{'estado':True, 'error':ErrorManager.get_error_by_code(NO_ERROR)})
                    else:
                        return return_object(**{'estado':False, 'error':ErrorManager.get_error_by_code(INSUFFICIENT_PERMISSIONS)})
                else:
                    return return_object(**{'estado':False, 'error':ErrorManager.get_error_by_code(INSTANCE_NOT_FOUND)})
            except Exception as e:
                return return_object(**{'estado':False, 'error':ErrorManager.get_error_by_code(error_code=UNKNOWN_ERROR,custom_message="Error Inesperado", custom_description=str(e))})
        else:
            return return_object(**{'estado':False, 'error':session_error})
    return mutate_delete_function

# fields to ignore getters

def get_fields_to_ignore(model_config, operation):
    fields_to_ignore=[]
    internal_field_resolvers=model_config.get('internal_field_resolvers')
    if operation in internal_field_resolvers.keys():
        fields_to_ignore+=list(internal_field_resolvers.get(operation).keys())
    if operation in model_config.get('exclude_fields_by_operation').keys():
        fields_to_ignore+=model_config.get('exclude_fields_by_operation').get(operation)
    return fields_to_ignore