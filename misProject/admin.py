from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from django.contrib import admin
from import_export.admin import ExportActionModelAdmin

admin.site.unregister(get_user_model())
admin.site.unregister(Group)


# Customizing the admin page in the management panel
@admin.register(get_user_model())
class CustomUserAdmin(UserAdmin, ExportActionModelAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups'),
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'last_login', 'date_joined', 'is_staff')


# Customizing the admin page in the management panel
@admin.register(Group)
class CustomGroupAdmin(GroupAdmin, ExportActionModelAdmin):
    exclude = ('permissions',)
