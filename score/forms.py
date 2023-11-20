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
        self.fields['questions'].required = True


class ScorePresentation(forms.ModelForm):
    def clean(self):
        """
        This is the function that can be used to
        validate your model data from admin
        """
        super(ScorePresentation, self).clean()
        # Examining student membership in the course
        new_presenters = self.cleaned_data['presenter']
        # self.cleaned_data['lesson'] = lesson instance
        lesson_users = User.objects.filter(groups__id=self.cleaned_data['lesson'].group.id)
        users_not_in_lesson = [i for i in new_presenters if i not in lesson_users]
        errors = {}
        if users_not_in_lesson:
            name_of_users_not_in_lesson = []
            for i in users_not_in_lesson:
                name_of_users_not_in_lesson.append(i.username)
                errors[
                    'presenter'] = f'افراد زیر در لیست دانشجویان این درس نیستند. نام کاربری ها: {name_of_users_not_in_lesson}'
        if errors:
            raise ValidationError(errors)


class ScoreScoreAdd(forms.ModelForm):
    class Meta:
        model = models.Score
        fields = '__all__'
