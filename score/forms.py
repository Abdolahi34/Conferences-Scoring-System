from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from score import models


class ScoreLesson(forms.ModelForm):
    class Meta:
        model = models.Lesson
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Compulsory selection of questions for the lesson
        # In order to create lessons by signal, without errors, (after saving the group model),
        # the forcing of the questions field has been removed
        self.fields['questions'].required = True


class ScorePresentation(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        forms.ModelForm.__init__(self, *args, **kwargs)
        # Placing the students of each course in the list of selectable people
        # In edit mode
        if 'instance' in kwargs.keys():
            # if instance not None
            if kwargs['instance']:
                lesson_users = User.objects.filter(groups__id=kwargs['instance'].lesson.group.id)
                self.fields['presenter'].queryset = lesson_users
                self.fields['absent'].queryset = lesson_users

    def clean(self):
        """
        This is the function that can be used to
        validate model data from admin
        """
        super(ScorePresentation, self).clean()

        # A function to check the membership of people in a particular course
        def membership_check(members, is_required=False):
            if members in self.cleaned_data.keys():
                new_members = self.cleaned_data[members]
                users_not_in_lesson = [i for i in new_members if i not in lesson_users]
                if users_not_in_lesson:
                    name_of_users_not_in_lesson = [i.username for i in users_not_in_lesson]
                    errors[
                        members] = f'افراد زیر در لیست دانشجویان این درس نیستند. نام کاربری ها: {name_of_users_not_in_lesson}'
            else:
                if is_required:
                    errors[members] = 'فردی انتخاب نشده است.'

        # Examining the membership of presenters and absentees in the course
        if 'lesson' in self.cleaned_data.keys():
            errors = {}
            lesson_users = User.objects.filter(groups__id=self.cleaned_data['lesson'].group.id)
            membership_check('presenter', True)
            membership_check('absent')
            if errors:
                raise ValidationError(errors)


class ScoreScoreAdd(forms.ModelForm):
    class Meta:
        model = models.Score
        fields = '__all__'
