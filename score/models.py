from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
import numpy
import logging

logger = logging.getLogger(__name__)


class Question(models.Model):
    class Meta:
        verbose_name = 'سوال'
        verbose_name_plural = 'سوالات'

    title = models.CharField(max_length=100, verbose_name='عنوان', help_text='عنوان نمایشی به جای لیست سوالات')
    question_list = ArrayField(models.CharField(max_length=200), verbose_name='سوالات ارزیابی ارائه')

    def __str__(self):
        return self.title

    def clean(self):
        errors = {}

        if len(self.question_list) != 5:
            errors['question_list'] = '5 سوال باید تعریف کنید'
        raise ValidationError(errors)


class Presentation(models.Model):
    class Meta:
        verbose_name = 'ارائه'
        verbose_name_plural = 'ارائه ها'

    lesson = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, verbose_name='نام گروه (درس)')
    subject = models.CharField(max_length=100, verbose_name='موضوع ارائه')
    presenter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='ارائه کننده')
    questions = models.ForeignKey(Question, on_delete=models.SET_NULL, null=True, verbose_name='سوالات ارزیابی ارائه')

    creator = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, editable=False,
                                verbose_name='سازنده', related_name='presentation_creator')
    latest_modifier = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, editable=False,
                                        verbose_name='آخرین تغییر دهنده', related_name='presentation_latest_modifier')
    date_created = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    date_modified = models.DateTimeField(auto_now=True, verbose_name='تاریخ آخرین تغییر')

    def __str__(self):
        return f'درس {self.lesson} - {self.subject}'

    def clean(self):
        errors = {}
        # بررسی اینکه دانشجویان فقط در درسی که اسمشان در آن هست بتوانند ارائه بدهند
        if self.presenter not in User.objects.filter(groups__name=self.lesson):
            errors['presenter'] = 'دانشجو مورد نظر در لیست دانشجویان این درس نیست'
        raise ValidationError(errors)


class Score(models.Model):
    class Meta:
        verbose_name = 'امتیاز'
        verbose_name_plural = 'امتیازات'

    presentation = models.ForeignKey(Presentation, on_delete=models.SET_NULL, null=True, editable=False,
                                     verbose_name='مشخصات ارائه', related_name='point_lesson')
    point_giver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False,
                                    verbose_name='امتیاز دهنده', related_name='point_point_giver')
    point_list = ArrayField(models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)]),
                            verbose_name='نمره سوالات')
    point_avr = models.FloatField(editable=False, blank=True, null=True)

    def clean(self):
        errors = {}
        if len(self.point_list) != 5:
            errors['point_list'] = 'به تمام سوالات باید امتیاز دهید'
        raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()

        # try:
        self.point_avr = numpy.average(self.point_list)
        # except Exception as e:
        #     logger.error('The try block part encountered an error: %s', str(e), exc_info=True)
        super(Point, self).save(*args, **kwargs)
