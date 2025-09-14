from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.core.cache import cache


class HasRole(BasePermission):
    """Require one of the Django Group names to access the view.

    Use by setting `required_roles = ['Admin', 'Registrar']` on the view.
    """

    def has_permission(self, request, view):
        roles = getattr(view, 'required_roles', None)
        user = request.user
        if not roles:
            return True
        if not user or not user.is_authenticated:
            return False
        # Try cached roles first (seeded by RolesPermissionsView); fallback to DB via groups
        cache_key = f"rolesperms:v2:{user.id}"
        cached = cache.get(cache_key)
        if cached and 'roles' in cached:
            user_roles = set(cached['roles'])
        else:
            user_roles = set(user.groups.values_list('name', flat=True))
        return any(r in user_roles for r in roles)


class HasAnyPermission(BasePermission):
    """Require any Django permission by fully qualified codename (app_label.codename).

    Set `required_permissions = ['students.view_student', 'fees.refund']` on the view.
    """

    def has_permission(self, request, view):
        perms = getattr(view, 'required_permissions', None)
        user = request.user
        if not perms:
            return True
        if not user or not user.is_authenticated:
            return False
        cache_key = f"rolesperms:v2:{user.id}"
        cached = cache.get(cache_key)
        if cached and 'permissions' in cached:
            user_perms = set(cached['permissions'])
        else:
            user_perms = set(user.get_all_permissions())
        return any(p in user_perms for p in perms)


