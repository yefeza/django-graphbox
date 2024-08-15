"""
Middleware to log `*/api/*` requests and responses.
"""

from django_graphbox.helpers.middlewares import MiddlewareSessionCollector


class GraphboxAuthMiddleware:
    """Graphbox Auth Middleware."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        session_manager = MiddlewareSessionCollector.get_session_manager(request.path)
        if session_manager != None:
            valid, actual_user, session_error = session_manager.preprocess_user_data(
                request
            )
            request.graphbox_auth_info = {
                "valid": valid,
                "user_instance": actual_user,
                "session_error": session_error,
            }

        # request passes on to controller
        response = self.get_response(request)
        return response
