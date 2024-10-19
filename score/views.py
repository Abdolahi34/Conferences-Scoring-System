from django.shortcuts import render, HttpResponse, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views import View
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.urls import reverse
import math

from score import models, forms


# Show the list of courses
def lessons_list(request):
    lessons = models.Lesson.objects.all()
    if lessons:
        args = {'lessons': lessons}
        return render(request, 'score/lessons_list.html', args)
    else:
        return render(request, 'score/lessons_list.html')


# Register points for presentation
@method_decorator(login_required, name="dispatch")
class RegisterScore(View):
    def get(self, *args, **kwargs):
        # Raise 404 error when not available
        lesson = get_object_or_404(models.Lesson, group_id=self.kwargs['group_id'])
        # If the question set was not defined for the course
        if not lesson.questions:
            args = {
                'message': 'سوالات ارزیابی، برای درس تعریف نشده است.',
                'url': reverse('score:lessons'),
            }
            return render(self.request, 'score/message_redirect.html', args)
        # Get active presentations inside this lesson
        presentations = models.Presentation.objects.filter(Q(lesson_id=lesson.id) & Q(is_active=True))
        if not presentations:
            args = {
                'message': 'ارائه ای یافت نشد.',
                'url': reverse('score:lessons'),
            }
            return render(self.request, 'score/message_redirect.html', args)
        # Examining student membership in the course
        this_user = User.objects.filter(Q(groups__id=self.kwargs['group_id']) & Q(id=self.request.user.id))
        if this_user:
            presentations_absent = []  # The id of the presentations I was absent
            args = {
                'score_list': {}
            }
            # Get all the points that the user has registered in this course
            scores = models.Score.objects.filter(
                Q(presentation__lesson_id=lesson.id) & Q(score_giver__user_id=self.request.user.id))
            for presentation in presentations:
                # Checking the presence of scores with the desired specifications (for editing)
                score_instance = scores.filter(presentation_id=presentation.id)
                # Specify the id of the presentations that the person was absent, to block scoring access
                absent_users = presentation.absent.all()
                if this_user[0] in absent_users:
                    presentations_absent.append(presentation.id)
                    # Delete the user's points to the course in which he was absent
                    score_instance.delete()
                # Score editing mode
                if score_instance:
                    args['score_list'][presentation.id] = score_instance[0].score_list
            # If all presentations have been absent
            if presentations.count() == len(presentations_absent):
                args = {
                    'message': 'شما تمام ارائه ها را غایب بودبد و مجاز به امتیازدهی نمی باشید.',
                    'url': reverse('score:lessons'),
                }
                return render(self.request, 'score/message_redirect.html', args)
            # Get information from the database to display on the site
            questions = lesson.questions.question_list
            preferential = models.Preferential.objects.get(Q(user_id=self.request.user.id) & Q(lesson_id=lesson.id))
            score_balance = preferential.score_balance
            score_balance_dict = {}
            for key in range(1, len(score_balance) + 1):
                score_balance_dict[key] = score_balance[key - 1]
            # Lack of access to scoring for absentees
            presentations = presentations.exclude(id__in=presentations_absent)
            args['presentations'] = presentations
            args['questions'] = questions
            args['score_balances'] = score_balance_dict
            args['has_card'] = True
            args['has_footer'] = True
            return render(self.request, 'score/register_score.html', args)
        else:
            args = {
                'message': 'شما عضو این درس نمی باشید.',
                'url': reverse('score:lessons'),
            }
            return render(self.request, 'score/message_redirect.html', args)

    def post(self, *args, **kwargs):
        posted_data = self.request.POST
        # Build a list (dict_values) of points received from request.POST
        score_text = len({key: value for key, value in posted_data.items() if 'question' in key})
        new_score_list = [int(i) for i in list(score_text)]
        score_instance = models.Score.objects.filter(
            Q(presentation_id=self.kwargs['presentation_id']) & Q(score_giver__user_id=self.request.user.id))
        lesson = models.Presentation.objects.get(id=self.kwargs['presentation_id']).lesson
        posted_data_reformatted = {
            "csrfmiddlewaretoken": posted_data['csrfmiddlewaretoken'],
            "presentation": self.kwargs['presentation_id'],
            "score_giver": models.Preferential.objects.get(Q(user_id=self.request.user.id) & Q(lesson_id=lesson.id)).id,
            "score_list": new_score_list,
        }
        # If there is a score instance, it edits it. Otherwise, it creates a new instance
        if score_instance:
            form = forms.ScoreScoreAdd(posted_data_reformatted, instance=score_instance[0])
        else:
            form = forms.ScoreScoreAdd(posted_data_reformatted)
        if form.is_valid():
            form.save()
            args = {
                'message': 'اطلاعات ذخیره شد.',
                'url': reverse('score:presentations', kwargs={'group_id': self.kwargs['group_id']}),
            }
            return render(self.request, 'score/message_redirect.html', args)
        presentation = models.Presentation.objects.get(id=self.kwargs['presentation_id'])
        questions = presentation.lesson.questions.question_list
        preferential = models.Preferential.objects.get(
            Q(user_id=self.request.user.id) & Q(lesson_id=presentation.lesson.id))
        score_balance = preferential.score_balance
        score_balance_dict = {}
        for key in range(1, len(score_balance) + 1):
            score_balance_dict[key] = score_balance[key - 1]
        args = {
            'presentation': presentation[0],
            'questions': questions,
            'score_balances': score_balance_dict,
            'score_list': new_score_list,
            'form': form,
            'has_card': True,
            'has_footer': True,
        }
        return render(self.request, 'score/register_score.html', args)


# Run every minute
def save_lessons_and_preferentials(request):
    lessons = models.Lesson.objects.all()
    for lesson in lessons:
        # Calculate and save the initial_score of lessons when saving a lesson
        lesson.save()
        # Calculation of preferentials
        lesson_users = User.objects.filter(groups__id=lesson.group.id)
        if lesson_users:
            # Preferential instances is based on 2 fields, user and lesson; Here we filter by lesson.
            lesson_preferentials = lesson.preferential_lesson.all()
            for lesson_user in lesson_users:
                # We filter the preferentials inside a lesson according to each user
                # the output will be a specific instance.
                preferential = lesson_preferentials.filter(user_id=lesson_user.id)
                if preferential:
                    preferential = preferential[0]
                else:
                    # Creating a Preferential instance with the highest score of this course for user
                    # who do not have a Preferential instance of this lesson
                    preferential = models.Preferential(user=lesson_user, lesson=lesson,
                                                       score_balance=lesson.initial_score)
                preferential.save()
        # Calculate the score of each presentation
        presentations = models.Presentation.objects.filter(lesson_id=lesson.id)
        for presentation in presentations:
            scores = presentation.score_presentation.all()
            if scores:
                score_sum = 0
                for score in scores:
                    for i in score.score_list:
                        score_sum += i
                # The sum of the points given / The number of scorers
                # Using the math module to round the score to 2 decimal places
                presentation.score_avr = math.ceil((score_sum / scores.count()) * 100) / 100
            else:
                presentation.score_avr = 0
            presentation.save()
    return HttpResponse('Everything was saved.')
