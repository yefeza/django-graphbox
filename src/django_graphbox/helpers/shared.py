# Dominant Access Group Getter

def get_access_group(operation, model_config):
    """ Get access group for operation based on model config 
    
    Args:
        operation (str): operation name
        model_config (dict): model config

    Returns:
        str: access group finaly selected for operation
    """
    if operation in model_config['access_by_operation']:
        return model_config['access_by_operation'][operation]
    return model_config['access_group']

# recursive logical expression evaluator for validators

def evaluate_result(operation, info, model_instance, **kwargs):
    """Evaluate result of operation validators and return a boolean result

    Args:
        operation (dict): operation validators config.
        info (dict): graphql.execution.base.ResolveInfo object.
        model_instance (object): model instance of operation.
        **kwargs (dict): kwargs input from graphql.
    Returns:
        bool: Result of evaluation of validators of operation config.
    """
    if 'validators' in operation:
        validators = operation['validators']
        if 'connector' in operation:
            connector = operation['connector']
        else:
            connector = 'AND'
        if connector == 'AND':
            result = True
            for validator in validators:
                if callable(validator):
                    result = result and validator(info, model_instance, **kwargs)
                else:
                    if validator==None:
                        raise Exception('Validator must be a callable or dict with validators and connector')
                    else:
                        result = result and evaluate_result(validator, info, model_instance, **kwargs)
            return result
        else:
            result = False
            for validator in validators:
                if callable(validator):
                    result = result or validator(info, model_instance, **kwargs)
                else:
                    if validator==None:
                        raise Exception('Validator must be a callable or dict with validators and connector')
                    else:
                        result = result or evaluate_result(validator, info, model_instance, **kwargs)
            return result
    else:
        return True

