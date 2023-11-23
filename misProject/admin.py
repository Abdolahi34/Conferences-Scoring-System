from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib import admin

from score import models

admin.site.unregister(get_user_model())


# Customizing the admin page in the management panel
@admin.register(get_user_model())
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'last_login', 'date_joined', 'is_staff')

    def save_model(self, request, obj, form, change):
        # Automatic creation of Preferential instance after creation of each user
        # if on update
        if 'groups' in form.cleaned_data:
            user_groups = form.cleaned_data['groups']
            for user_group in user_groups:
                lesson = models.Lesson.objects.filter(group_id=user_group.id)
                if lesson:
                    lesson = lesson[0]
                else:
                    user_group.save()
                    lesson = user_group.lesson_group
                models.set_preferential(lesson, lesson.initial_score)
        super(CustomUserAdmin, self).save_model(request, obj, form, change)
