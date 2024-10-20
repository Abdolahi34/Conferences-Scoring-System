from django.db import models
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import ArrayField
from django_jsonform.models.fields import ArrayField as ArrayField_djf
from django.db.models import Q
import math


class Question(models.Model):
    class Meta:
        verbose_name = 'مجموعه سوال'
        verbose_name_plural = 'مجموعه سوالات'

    title = models.CharField(max_length=100, unique=True, verbose_name='عنوان',
                             help_text='عنوان نمایشی به جای لیست سوالات')
    question_list = ArrayField_djf(models.CharField(max_length=200), verbose_name='سوالات ارزیابی ارائه')
    min_score = models.IntegerField(default=0, verbose_name='حداقل امتیاز',
                                    help_text='حداقل امتیازی که میتوانید وارد کنید 0 است')
    max_score = models.IntegerField(default=10, verbose_name='حداکثر امتیاز')
    # Confidential information fields
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False,
                                verbose_name='سازنده', related_name='question_creator')
    latest_modifier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False,
                                        verbose_name='آخرین تغییر دهنده', related_name='question_latest_modifier')
    date_created = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    date_modified = models.DateTimeField(auto_now=True, verbose_name='تاریخ آخرین تغییر')

    def __str__(self):
        return self.title

    def clean(self):
        errors = {}
        if not self.question_list:
            errors['question_list'] = 'حداقل یک سوال باید تعریف کنید'
        if not self.min_score < self.max_score:
            errors['min_score'] = 'حداقل امتیاز باید از حداکثر کمتر باشد'
            errors['max_score'] = 'حداقل امتیاز باید از حداکثر کمتر باشد'
        if self.min_score < 0:
            errors['min_score'] = 'حداقل امتیاز نمی تواند منفی باشد'
        raise ValidationError(errors)


# Lesson model according to Group model
class Lesson(models.Model):
    class Meta:
        verbose_name = 'درس'
        verbose_name_plural = 'دروس'

    group = models.OneToOneField(Group, on_delete=models.CASCADE, editable=False, verbose_name='گروه',
                                 related_name='lesson_group')
    questions = models.ForeignKey(Question, on_delete=models.SET_NULL, blank=True, null=True,
                                  verbose_name='سوالات ارزیابی ارائه', related_name='lesson_questions')
    # The maximum score that can be used by the user for each question of each lesson
    initial_score = ArrayField(models.PositiveIntegerField(default=0), editable=False, blank=True, null=True,
                               verbose_name='امتیاز اولیه هر کاربر')

    def __str__(self):
        return f"درس {self.group}"

    def save(self, *args, **kwargs):
        self.full_clean()
        """
        Different modes of initial_score:
        1. The set of questions for the lesson is not defined.
        Output: None
        2. There is no presentation for the lesson.
        Output: [0, 0 ... 0] (puts 0 in the list to the number of questions.)
        3. At least one presentation and set of questions should be defined for the lesson.
        Output: list of initial user scores.
        """
        # Lesson initial_score calculation on edit mode
        if self.id and self.questions:
            presentations_count = self.presentation_lesson.all().count()
            # if presentations_count != 0
            if presentations_count:
                max_score = self.questions.max_score
                min_score = self.questions.min_score
                score_amount = max_score - min_score
                # usable initial score = rounding(2/3 * Number of presentations * maximum score - minimum score of each question of the lesson)
                initial_score = math.ceil(0.666 * presentations_count * score_amount)
            else:
                initial_score = 0
            question_count = len(self.questions.question_list)
            self.initial_score = [initial_score for _ in range(question_count)]  # The final list of scores
        else:
            self.initial_score = None
        super(Lesson, self).save(*args, **kwargs)


# Preferential model according to User model
class Preferential(models.Model):
    class Meta:
        verbose_name = 'امتیاز دهنده'
        verbose_name_plural = 'امتیاز دهندگان'

    # The user's remaining score of each question in each lesson
    # which user?
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='preferential_user')
    # which lesson?
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='preferential_lesson')
    # what grades?
    score_balance = ArrayField(models.IntegerField(default=0), blank=True, null=True)

    def __str__(self):
        return f"کاربر {self.user} - {self.lesson}"

    def save(self, *args, **kwargs):
        self.full_clean()
        # set score_balance of Preferential
        # score_balance = copy of self.lesson.initial_score
        if self.lesson.initial_score:
            score_balance = [i for i in self.lesson.initial_score]
            scores = Score.objects.filter(
                Q(score_giver__user_id=self.user.id) & Q(presentation__lesson_id=self.lesson.id))
            for score in scores:
                # List of final scores minus scores spent
                for i in range(len(score.score_list)):
                    score_balance[i] -= score.score_list[i]
            self.score_balance = score_balance
        super(Preferential, self).save(*args, **kwargs)


class Presentation(models.Model):
    class Meta:
        verbose_name = 'ارائه'
        verbose_name_plural = 'ارائه ها'

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True, verbose_name='نام گروه (درس)',
                               related_name='presentation_lesson')
    subject = models.CharField(max_length=100, verbose_name='موضوع ارائه',
                               help_text='موضوع ارائه در هر درس باید یکتا باشد')
    is_active = models.BooleanField(default=False, verbose_name='وضعیت ارائه')
    presenter = models.ManyToManyField(User, verbose_name='ارائه کنندگان', related_name='Presentation_presenter',
                                       help_text='درصورت تغییر درس، یکبار ارائه را ذخیره کنید، تا دانشجویان درسی که انتخاب کردید نمایش داده شوند.<br>')
    absent = models.ManyToManyField(User, blank=True, verbose_name='غایبین', related_name='Presentation_absent',
                                    help_text='درصورت تغییر درس، یکبار ارائه را ذخیره کنید، تا دانشجویان درسی که انتخاب کردید نمایش داده شوند.<br>')
    score_avr = models.FloatField(default=0, editable=False, blank=True, null=True, verbose_name='امتیاز ارائه')
    # Confidential information fields
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False,
                                verbose_name='سازنده', related_name='presentation_creator')
    latest_modifier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False,
                                        verbose_name='آخرین تغییر دهنده', related_name='presentation_latest_modifier')
    date_created = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    date_modified = models.DateTimeField(auto_now=True, verbose_name='تاریخ آخرین تغییر')

    def __str__(self):
        return f'{self.lesson} - موضوع {self.subject}'

    def clean(self):
        # Validation of student membership in the course is done in the forms.py file
        # Validation of the uniqueness of the subject in each lesson
        if self.lesson:
            errors = {}
            presentations = Presentation.objects.filter(lesson_id=self.lesson.id)
            for i in presentations:
                if i.subject == self.subject and i.id != self.id:
                    errors['subject'] = 'موضوع در هردرس باید یکتا باشد'
                    break
            raise ValidationError(errors)


class Score(models.Model):
    class Meta:
        verbose_name = 'امتیاز'
        verbose_name_plural = 'امتیازات'

    presentation = models.ForeignKey(Presentation, on_delete=models.CASCADE, null=True, verbose_name='مشخصات ارائه',
                                     related_name='score_presentation')
    score_giver = models.ForeignKey(Preferential, on_delete=models.CASCADE, null=True, verbose_name='امتیاز دهنده',
                                    related_name='score_score_giver')
    score_list = ArrayField(models.PositiveIntegerField(), verbose_name='نمره سوالات')
    # Confidential information fields
    date_created = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    date_modified = models.DateTimeField(auto_now=True, verbose_name='تاریخ آخرین تغییر')

    def __str__(self):
        return f'امتیاز ({self.score_giver}) به {self.presentation}'

    def clean(self):
        errors = {}
        # Instead of validating the scoring of all questions, all score fields were required in the html file.
        # Validation of the given score range
        min_score = self.presentation.lesson.questions.min_score
        max_score = self.presentation.lesson.questions.max_score
        for i in self.score_list:
            if not min_score <= i <= max_score:
                errors['score_list'] = [f'امتیازات وارد شده باید بین بازه {min_score} تا {max_score} باشد']
                break
        # Checking student membership in the course is done in views.py.
        # Validate that the scores entered are less than or equal to the scores balance
        score_balance = self.score_giver.score_balance  # Remaining scores in this lesson
        wrong_scores_list_index = []
        if self.id:
            saved_score_list = Score.objects.get(id=self.id).score_list
        for i in range(len(score_balance)):
            if self.id:
                if score_balance[i] + saved_score_list[i] < self.score_list[i]:
                    wrong_scores_list_index.append(i + 1)
            else:
                if score_balance[i] < self.score_list[i]:
                    wrong_scores_list_index.append(i + 1)
        if wrong_scores_list_index:
            if 'score_list' in errors.keys():
                errors['score_list'].append(
                    f'امتیاز های وارد شده روی سوالات شماره {wrong_scores_list_index} بیشتر از موجودی شماست')
            else:
                errors[
                    'score_list'] = f'امتیاز های وارد شده روی سوالات شماره {wrong_scores_list_index} بیشتر از موجودی شماست'
        raise ValidationError(errors)
