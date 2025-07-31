# Dominant Access Group Getter


def get_access_group(operation, model_config):
    """Get access group for operation based on model config

    Args:
        operation (str): operation name
        model_config (dict): model config

    Returns:
        str: access group finaly selected for operation
    """
    if operation in model_config["access_by_operation"]:
        return model_config["access_by_operation"][operation]
    return model_config["access_group"]


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
    if "validators" in operation:
        validators = operation["validators"]
        if "connector" in operation:
            connector = operation["connector"]
        else:
            connector = "AND"
        if connector == "AND":
            result = True
            for validator in validators:
                if callable(validator):
                    result = result and validator(info, model_instance, **kwargs)
                else:
                    if validator == None:
                        raise Exception(
                            "Validator must be a callable or dict with validators and connector"
                        )
                    else:
                        result = result and evaluate_result(
                            validator, info, model_instance, **kwargs
                        )
            return result
        else:
            result = False
            for validator in validators:
                if callable(validator):
                    result = result or validator(info, model_instance, **kwargs)
                else:
                    if validator == None:
                        raise Exception(
                            "Validator must be a callable or dict with validators and connector"
                        )
                    else:
                        result = result or evaluate_result(
                            validator, info, model_instance, **kwargs
                        )
            return result
    else:
        return True


# Convert camel case to snake case
import re


def camel_to_snake(name):
    """Convert camel case to snake case"""
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


# Convert custom order fields to django order fields


def convert_custom_ordering_fields(custom_ordering_fields):
    """Convert custom ordering fields list like ['fieldName1.asc', 'fieldName2.desc'] to django ordering fields list like ['field_name1', '-field_name2']"""
    if custom_ordering_fields != None:
        ordering_field = []
        for custom_ordering_field in custom_ordering_fields:
            if "." in custom_ordering_field:
                field_name, order = custom_ordering_field.split(".")
                field_name = camel_to_snake(field_name)
                if order == "asc":
                    ordering_field.append(field_name)
                elif order == "desc":
                    ordering_field.append("-" + field_name)
                else:
                    raise Exception("Order must be asc or desc")
            else:
                ordering_field.append(custom_ordering_field)
        return ordering_field
