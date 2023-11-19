from django.contrib import admin

from score import models, forms


@admin.register(models.Question)
class QuestionAdmin(admin.ModelAdmin):
    search_fields = ['title', 'question_list', 'creator', 'latest_modifier', 'date_created', 'date_modified']
    list_per_page = 20
    list_display = ['title', 'creator', 'latest_modifier', 'date_created', 'date_modified']
    ordering = ['-id']

    def save_model(self, request, obj, form, change):
        # Set creator and latest modifier when saving each menu item
        if obj.creator_id is None:
            obj.creator = request.user
        obj.latest_modifier = request.user
        super(QuestionAdmin, self).save_model(request, obj, form, change)


@admin.register(models.Lesson)
class LessonAdmin(admin.ModelAdmin):
    form = forms.ScoreLesson


@admin.register(models.Presentation)
class PresentationAdmin(admin.ModelAdmin):
    list_filter = ['lesson', 'is_active']
    search_fields = ['lesson', 'subject', 'presenter', 'questions', 'is_active', 'creator', 'latest_modifier',
                     'date_created', 'date_modified']
    list_per_page = 20
    list_display = ['lesson', 'subject', 'is_active', 'creator', 'latest_modifier', 'date_created', 'date_modified']
    ordering = ['-is_active', '-id']
    list_display_links = ['lesson', 'subject']
    filter_horizontal = ['presenter']
    # To validate some fields
    form = forms.ScorePresentation

    def save_model(self, request, obj, form, change):
        # Set creator and latest modifier when saving each menu item
        if obj.creator_id is None:
            obj.creator = request.user
        obj.latest_modifier = request.user
        super(PresentationAdmin, self).save_model(request, obj, form, change)
