from django.urls import path
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView, MeView, LogoutView, RateLimitedTokenView, RateLimitedRefreshView,
    RolesPermissionsView, UserListView, AssignRoleView, RevokeRoleView, RolesCatalogView,
    MySessionsView, MyActiveSessionView,
)


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', MeView.as_view(), name='me'),
    # Compatibility endpoints expected by some clients
    path('user/', lambda request: JsonResponse({'detail': 'Use /api/accounts/me/'}, status=404), name='auth_user_compat'),
    path('session/', lambda request: JsonResponse({'detail': 'Use /api/accounts/me/session/active/'}, status=404), name='auth_session_compat'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/', RateLimitedTokenView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', RateLimitedRefreshView.as_view(), name='token_refresh'),
    path('me/roles-permissions/', RolesPermissionsView.as_view(), name='me_roles_permissions'),
    path('users/', UserListView.as_view(), name='users_list'),
    path('roles/assign/', AssignRoleView.as_view(), name='assign_role'),
    path('roles/revoke/', RevokeRoleView.as_view(), name='revoke_role'),
    path('roles/catalog/', RolesCatalogView.as_view(), name='roles_catalog'),
    path('me/sessions/', MySessionsView.as_view(), name='me_sessions'),
    path('me/session/active/', MyActiveSessionView.as_view(), name='me_session_active'),
]


