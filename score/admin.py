from django.contrib import admin

from score import models, forms


@admin.register(models.Question)
class QuestionAdmin(admin.ModelAdmin):
    search_fields = [i.name for i in models.Question._meta.fields if i.name != 'id']
    list_per_page = 10
    list_display = [i.name for i in models.Question._meta.fields if i.name not in ['id', 'question_list']]
    ordering = ['-id']

    def save_model(self, request, obj, form, change):
        # Set creator and latest modifier when saving each menu item
        if obj.creator_id is None:
            obj.creator = request.user
        obj.latest_modifier = request.user
        super(QuestionAdmin, self).save_model(request, obj, form, change)


@admin.register(models.Lesson)
class LessonAdmin(admin.ModelAdmin):
    search_fields = [i.name for i in models.Lesson._meta.fields if i.name != 'id']
    list_per_page = 10
    list_display = [i.name for i in models.Lesson._meta.fields if i.name != 'id']
    ordering = ['-id']
    form = forms.ScoreLesson

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(models.Presentation)
class PresentationAdmin(admin.ModelAdmin):
    list_filter = ['lesson', 'is_active']
    search_fields = [i.name for i in models.Presentation._meta.fields if i.name != 'id']
    list_per_page = 10
    list_display = [i.name for i in models.Presentation._meta.fields if i.name not in ['id', 'presenter', 'absent']]
    ordering = ['-is_active', '-id']
    list_display_links = ['lesson', 'subject']
    filter_horizontal = ['presenter', 'absent']
    # To validate some fields
    form = forms.ScorePresentation

    def save_model(self, request, obj, form, change):
        # Set creator and latest modifier when saving each menu item
        if obj.creator_id is None:
            obj.creator = request.user
        obj.latest_modifier = request.user
        super(PresentationAdmin, self).save_model(request, obj, form, change)
