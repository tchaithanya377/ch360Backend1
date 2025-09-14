from django.contrib import admin
from django.contrib.auth.models import Group
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from .models import (
    User,
    Role,
    Permission,
    RolePermission,
    UserRole,
    AuthIdentifier,
    FailedLogin,
    PasswordReset,
    MfaSetup,
    UserSession,
    AuditLog,
)
from .forms import UserCreationForm, UserChangeForm


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'is_active', 'is_staff', 'is_verified', 'last_login')
    search_fields = ('email', 'username')
    # Keep Groups visible; hide granular user_permissions for simplicity
    exclude = ('user_permissions',)

    add_form = UserCreationForm
    form = UserChangeForm

    change_form_template = 'admin/accounts/user/change_form.html'

    fieldsets = (
        (None, {
            'fields': ('email', 'username')
        }),
        ('Status', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'must_change_password')
        }),
        ('Timestamps', {
            'fields': ('last_login', 'date_joined')
        }),
        ('Groups', {
            'fields': ('groups',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'is_active', 'is_staff', 'is_superuser', 'password1', 'password2'),
        }),
    )

    readonly_fields = ('last_login', 'date_joined')

    actions = ['reset_passwords_to_default']

    def reset_passwords_to_default(self, request, queryset):
        count = 0
        for user in queryset:
            user.set_password('Campus@360')
            user.must_change_password = True
            user.save()
            count += 1
        self.message_user(request, f'Successfully reset passwords for {count} users to the default.')
    reset_passwords_to_default.short_description = 'Reset passwords to default (Campus@360)'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/reset-password/', self.admin_site.admin_view(self.reset_single_password), name='accounts_user_reset_password'),
        ]
        return custom_urls + urls

    def reset_single_password(self, request, object_id):
        try:
            user = User.objects.get(pk=object_id)
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('admin:accounts_user_changelist')
        user.set_password('Campus@360')
        user.must_change_password = True
        user.save()
        messages.success(request, f"Password for {user.email or user.username} has been reset to default (Campus@360).")
        return redirect(f'../')


admin.site.unregister = getattr(admin.site, 'unregister', lambda model: None)

# Hide custom RBAC models from admin menu to avoid duplication; manage via Django Groups instead
try:
    from .models import Role, Permission as CustomPermission, RolePermission, UserRole
    for mdl in (Role, CustomPermission, RolePermission, UserRole):
        try:
            admin.site.unregister(mdl)
        except Exception:
            pass
except Exception:
    pass

# Keep operational/auth tables visible as needed
admin.site.register(AuthIdentifier)
admin.site.register(FailedLogin)
admin.site.register(PasswordReset)
admin.site.register(MfaSetup)
admin.site.register(UserSession)
admin.site.register(AuditLog)


# Ensure Django Group admin remains available (do not unregister)

