# graphene imports
import graphene
# shared helpers
from django_graphbox.helpers.shared import *
# django imports
from django.db.models import Q

# query resolver builders
def build_field_by_id_resolver(self):
    def field_resolver_function(parent, info, **kwargs):
        # get model config by this path
        operation_name=info.operation.selection_set.selections[0].name.value.lower()
        config=self._models_by_op_name[operation_name]
        # get access group for validate access
        access_group=get_access_group('field_by_id', config)
        if self._session_manager!=None:
            valid, actual_user_instance, error=self._session_manager.validate_access(info.context, access_group)
        else:
            valid=True
        if valid:
            model=config.get('model')
            result=model.objects.get(id=kwargs.get('id'))
            valid_operation=True
            if 'field_by_id' in config['validators_by_operation']:
                valid_operation=evaluate_result(config['validators_by_operation']['field_by_id'], info, result, **kwargs)
            if valid_operation:
                callbacks=config.get('callbacks_by_operation').get('field_by_id')
                if callbacks is not None:
                    for callback in callbacks:
                        if callable(callback):
                            callback(info, result, **kwargs)
                return result
        return None
    return field_resolver_function

def build_field_list_resolver(self):
    def list_resolver_function(parent, info, **kwargs):
        operation_name=info.operation.selection_set.selections[0].name.value.lower()
        config=self._models_by_op_name[operation_name]
        pagination_length=config.get('pagination_length')
        pagination_style=config.get('pagination_style')
        paginated_type=config.get('paginated_type')
        external_filters=config.get('external_filters')
        internal_filters=config.get('internal_filters')
        filters_operator=config.get('filters_operator')
        query_object=None
        for filter_config in external_filters:
            param_value=kwargs.get(filter_config.get('param_name'))
            if param_value is not None:
                if query_object is None:
                    query_object=Q(**{filter_config.get('field_name'): param_value})
                else:
                    query_object.add(Q(**{filter_config.get('field_name'): param_value}), filters_operator)
        for filter_config in internal_filters:
            resolver_filter=filter_config.get('resolver_filter')
            on_return_none=filter_config.get('on_return_none')
            value_filter=resolver_filter(info, **kwargs)
            if value_filter==None:
                if on_return_none=='skip':
                    continue
                elif on_return_none=='set__isnull':
                    if query_object is None:
                        query_object=Q(**{f"{filter_config.get('field_name')}__isnull": True})
                    else:
                        query_object.add(Q(**{f"{filter_config.get('field_name')}__isnull": True}), filters_operator)
            else:
                if query_object is None:
                    query_object=Q(**{filter_config.get('field_name'): value_filter})
                else:
                    query_object.add(Q(**{filter_config.get('field_name'): value_filter}), filters_operator)
        if query_object is None:
            query_object=Q()
        # get access group for validate access
        access_group=get_access_group('list_field', config)
        if self._session_manager!=None:
            valid, actual_user_instance, error=self._session_manager.validate_access(info.context, access_group)
        else:
            valid=True
        if valid:
            model=config.get('model')
            if pagination_length == 0:
                result=model.objects.filter(query_object)
                callbacks=config.get('callbacks_by_operation').get('list_field')
                if callbacks is not None:
                    for callback in callbacks:
                        if callable(callback):
                            callback(info, result, **kwargs)
                return result
            else:
                pagina=kwargs.get('page')
                inicio=(pagina*pagination_length)-pagination_length
                fin=inicio+pagination_length
                items=model.objects.filter(query_object)[inicio:fin]
                callbacks=config.get('callbacks_by_operation').get('list_field')
                if callbacks is not None:
                    for callback in callbacks:
                        if callable(callback):
                            callback(info, items, **kwargs)
                if pagination_style=='infinite':
                    return items
                else:
                    total_items=model.objects.filter(query_object).count()
                    total_pages=total_items//pagination_length
                    if total_items%pagination_length>0:
                        total_pages+=1
                    has_next_page = pagina<total_pages
                    has_previous_page = pagina>1
                    return paginated_type(items=items, has_next_page=has_next_page, has_previous_page=has_previous_page, total_pages=total_pages, total_items=total_items)
        return None
    return list_resolver_function

# filters_args getter

def get_filters_args(model_config):
    filters_args={}
    external_filters=model_config.get('external_filters')
    for filter_config in external_filters:
        filters_args[filter_config.get('param_name')]=filter_config.get('param_type')
    if model_config.get('pagination_length') != 0:
        filters_args['page']=graphene.Int(required=True)
    return filters_args

# return objects by pagination style

def get_return_object(model_config):
    filters_args=get_filters_args(model_config)
    if model_config.get('pagination_length')==0  or model_config.get('pagination_style') == 'infinite':
        return_object=graphene.List(model_config['type'], filters_args)
    elif model_config.get('pagination_length')>0 and model_config.get('pagination_style') == 'paginated':
        return_object=graphene.Field(model_config['paginated_type'], filters_args)
    else:
        raise Exception(f"Unknown pagination style {model_config.get('pagination_style')}")
    return return_object