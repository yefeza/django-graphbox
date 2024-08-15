class MiddlewareSessionCollector:
    session_managers = {}

    @classmethod
    def register(cls, session_manager, schema_path):
        cls.session_managers[schema_path] = session_manager

    @classmethod
    def get_session_manager(cls, schema_path):
        if schema_path.startswith("/"):
            schema_path = schema_path[1:]
        if not schema_path.endswith("/"):
            schema_path = schema_path + "/"
        return cls.session_managers.get(schema_path, None)
