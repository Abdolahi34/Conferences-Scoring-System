from django.db import models
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db.models import Q
import math


# Lesson initial_score recalculation
def get_lesson_initial_score_list(lesson_ins):
    """
    lesson_ins: Lesson (object)
    """
    presentations_count = lesson_ins.presentation_lesson.all().count()
    if lesson_ins.questions:
        max_score = lesson_ins.questions.max_score
        min_score = lesson_ins.questions.min_score
        score_amount = max_score - min_score
        # if presentations_count != 0
        if presentations_count:
            # usable initial score = rounding(2/3 * Number of presentations * maximum score - minimum score of each lesson question)
            initial_score = math.ceil(0.666 * presentations_count * score_amount)
        else:
            initial_score = 0
        question_count = len(lesson_ins.questions.question_list)
        # return initial_score_list
        return [initial_score for i in range(question_count)]  # The final score list
    else:
        return []


# Creation or editing of Preferential instance, for users of certain courses, or courses of desired users
def set_preferential(lesson_ins, initial_score_list):
    """
    lesson_ins: Lesson (object)
    """
    lesson_users = User.objects.filter(groups__id=lesson_ins.group.id)
    if lesson_users:
        lesson_preferentials = lesson_ins.preferential_lesson.all()
        for lesson_user in lesson_users:
            preferential = lesson_preferentials.filter(user_id=lesson_user.id)
            if preferential:
                preferential = preferential[0]
                scores = Score.objects.filter(
                    Q(score_giver__user_id=lesson_user.id) & Q(presentation__lesson_id=lesson_ins.id))
                for score in scores:
                    # List of final scores minus scores spent
                    i = 0
                    for j in score.score_list:
                        initial_score_list[i] -= j
                        i += 1
                preferential.score_balance = initial_score_list
            else:
                # Creating a Preferential instance with the highest score of this course for user
                # who do not have a Preferential instance of this lesson
                preferential = Preferential(user=lesson_user, lesson=lesson_ins,
                                            score_balance=initial_score_list)
            preferential.save()


class Question(models.Model):
    class Meta:
        verbose_name = 'سوال'
        verbose_name_plural = 'سوالات'

    title = models.CharField(max_length=100, unique=True, verbose_name='عنوان',
                             help_text='عنوان نمایشی به جای لیست سوالات')
    question_list = ArrayField(models.CharField(max_length=200), verbose_name='سوالات ارزیابی ارائه',
                               help_text='بین سوالات از , (کاما) استفاده کنید.')  # TODO change help_text after create adminPanel
    min_score = models.IntegerField(default=0, verbose_name='حداقل امتیاز قابل ثبت برای سوالات',
                                    help_text='حداقل امتیازی که میتوانید وارد کنید 0 است')
    max_score = models.IntegerField(default=10, verbose_name='حداکثر امتیاز قابل ثبت برای سوالات')
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
        if len(self.question_list) < 1:
            errors['question_list'] = 'حداقل یک سوال باید تعریف کنید'
        if not self.min_score < self.max_score:
            errors['min_score'] = 'حداقل امتیاز باید از حداکثر کمتر باشد'
            errors['max_score'] = 'حداقل امتیاز باید از حداکثر کمتر باشد'
        if self.min_score < 0:
            errors['min_score'] = 'حداقل امتیاز نمی تواند منفی باشد'
        raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        # the effect of changing the score range of the questions on the ceiling of each user's score
        if self.id:
            lessons = self.lesson_questions.all()
            for lesson in lessons:
                lesson.save()
        super(Question, self).save(*args, **kwargs)


# Lesson model according to Group model
class Lesson(models.Model):
    class Meta:
        verbose_name = 'درس'
        verbose_name_plural = 'درس ها'

    group = models.OneToOneField(Group, on_delete=models.CASCADE, editable=False, related_name='lesson_group')
    questions = models.ForeignKey(Question, on_delete=models.SET_NULL, blank=True, null=True,
                                  verbose_name='سوالات ارزیابی ارائه', related_name='lesson_questions')
    # The maximum score that can be used by the user for each question of each lesson
    initial_score = ArrayField(models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0)]),
                               editable=False, blank=True, null=True)

    def __str__(self):
        return f"درس {self.group}"

    def save(self, *args, **kwargs):
        self.full_clean()
        # set initial_score of Lesson
        if self.id:
            initial_score_list = get_lesson_initial_score_list(self)
            self.initial_score = initial_score_list
            set_preferential(self, initial_score_list)
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
    score_balance = ArrayField(models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0)]),
                               blank=True, null=True)

    def __str__(self):
        return f"کاربر {self.user} - {self.lesson}"

    def save(self, *args, **kwargs):
        self.full_clean()
        # This is a customized copy of the set_preferential function
        # set score_balance of Preferential
        initial_score_list = self.lesson.initial_score
        scores = Score.objects.filter(Q(score_giver__user_id=self.user.id) & Q(presentation__lesson_id=self.lesson.id))
        for score in scores:
            # List of final scores minus scores spent
            i = 0
            for j in score.score_list:
                initial_score_list[i] -= j
                i += 1
        self.score_balance = initial_score_list
        super(Preferential, self).save(*args, **kwargs)


class Presentation(models.Model):
    class Meta:
        verbose_name = 'ارائه'
        verbose_name_plural = 'ارائه ها'

    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, verbose_name='نام گروه (درس)',
                               related_name='presentation_lesson')
    subject = models.CharField(max_length=100, verbose_name='موضوع ارائه',
                               help_text='موضوع ارائه در هر درس باید یکتا باشد')
    presenter = models.ManyToManyField(User, verbose_name='ارائه کنندگان', related_name='Presentation_presenter')
    is_active = models.BooleanField(default=False, verbose_name='وضعیت ارائه')
    score_avr = models.FloatField(default=0, editable=False, blank=True, null=True)
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
        errors = {}
        presentations = Presentation.objects.filter(lesson_id=self.lesson.id)
        for i in presentations:
            if i.subject == self.subject:
                if i.id != self.id:
                    errors['subject'] = 'موضوع در هردرس باید یکتا باشد'
                    break
        raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        # The effect of changing the number of presentations on the score ceiling of each question from the presentation
        self.lesson.save()
        super(Presentation, self).save(*args, **kwargs)


class Score(models.Model):
    class Meta:
        verbose_name = 'امتیاز'
        verbose_name_plural = 'امتیازات'

    presentation = models.ForeignKey(Presentation, on_delete=models.SET_NULL, null=True, verbose_name='مشخصات ارائه',
                                     related_name='score_presentation')
    score_giver = models.ForeignKey(Preferential, on_delete=models.SET_NULL, null=True, verbose_name='امتیاز دهنده',
                                    related_name='score_score_giver')
    score_list = ArrayField(models.PositiveSmallIntegerField(), verbose_name='نمره سوالات')

    def __str__(self):
        return f'امتیاز ({self.score_giver}) به {self.presentation}'

    def clean(self):
        errors = {}
        # Instead of validating the scoring of all questions, all score fields were required in the html file.
        # Validation of the given score range
        for i in self.score_list:
            if not self.presentation.lesson.questions.min_score <= i <= self.presentation.lesson.questions.max_score:
                errors[
                    'score_list'] = f'امتیازات وارد شده باید بین بازه {self.presentation.lesson.questions.min_score} تا {self.presentation.lesson.questions.max_score} باشد'
                break
        # Examining student membership in the course
        lesson_users = User.objects.filter(groups__id=self.presentation.lesson.group.id)
        if self.score_giver.user not in lesson_users:
            errors['score_giver'] = f'یوزر {self.score_giver.user.username} عضو درس موردنظر نمی باشد'
        # Validate that the scores entered are less than or equal to the scores balance
        if not errors:
            # Remaining scores in this lesson
            score_balance = self.score_giver.score_balance
            wrong_scores_list_index = []
            for i in range(len(score_balance)):
                if score_balance[i] < self.score_list[i]:
                    wrong_scores_list_index.append(i + 1)
            errors[
                'score_list'] = f'امتیاز های وارد شده روی سوالات شماره {wrong_scores_list_index} بیشتر از موجودی شماست'
        raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        # Record the change of the user's score_balance in that course
        set_preferential(self.presentation.lesson, self.presentation.lesson.initial_score)
        super(Score, self).save(*args, **kwargs)
