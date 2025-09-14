from django.utils.deprecation import MiddlewareMixin
from django.db import connection
from django.conf import settings


class SetCurrentDepartmentMiddleware(MiddlewareMixin):
    """Sets app.current_department for RLS policies.

    Source: request header 'X-Department-ID' or None.
    Only active if settings.ENABLE_RLS is True.
    """

    def process_request(self, request):
        if not getattr(settings, "ENABLE_RLS", False):
            return None
        dept_id = request.META.get('HTTP_X_DEPARTMENT_ID', '')
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('app.current_department', %s, false)", [dept_id])
        return None


