from django.shortcuts import render, HttpResponse, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views import View
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.urls import reverse

from score import models, forms


# TODO نمودار ارائه همه دروس
def score_chart(request):
    pass


# Show the list of courses
@login_required
def lessons_list(request):
    lessons = models.Lesson.objects.all()
    if lessons.exists():
        args = {'lessons': lessons}
        return render(request, 'score/lessons_list.html', args)
    else:
        args = {
            'message': 'درسی یافت نشد.',
            'url': reverse('score:score_chart'),
        }
        return render(request, 'score/message_redirect.html', args)


# Display the list of presentations of each course
@login_required
def presentations_list(request, group_id):
    # Raise 404 error when not available
    get_object_or_404(models.Lesson, group_id=group_id)
    # Examining student membership in the course
    if User.objects.filter(Q(groups__id=group_id) & Q(id=request.user.id)).exists():
        presentations = models.Presentation.objects.filter(Q(lesson__group_id=group_id) & Q(is_active=True))
        # Checking the existence and activeness of the presentation
        if presentations.exists():
            lesson = models.Lesson.objects.get(group_id=group_id)
            args = {'lesson': lesson, 'presentations': presentations}
            return render(request, 'score/presentations_list.html', args)
        else:
            args = {
                'message': 'ارائه ای یافت نشد.',
                'url': reverse('score:lessons'),
            }
            return render(request, 'score/message_redirect.html', args)
    else:
        args = {
            'message': 'شما عضو این درس نمی باشید.',
            'url': reverse('score:lessons'),
        }
        return render(request, 'score/message_redirect.html', args)


# Register points for presentation
@method_decorator(login_required, name="dispatch")
class RegisterScore(View):
    def get(self, *args, **kwargs):
        # Raise 404 error when not available
        get_object_or_404(models.Lesson, group_id=self.kwargs['group_id'])
        # Examining student membership in the course
        if User.objects.filter(Q(groups__id=self.kwargs['group_id']) & Q(id=self.request.user.id)).exists():
            # Lack of access to scoring for absentees
            this_user = User.objects.get(id=self.request.user.id)
            absent_users = models.Presentation.objects.get(id=self.kwargs['presentation_id']).absent.all()
            if this_user not in absent_users:
                presentation = models.Presentation.objects.filter(
                    Q(id=self.kwargs['presentation_id']) & Q(is_active=True))
                # Checking the existence and activeness of the presentation
                if presentation.exists():
                    questions = presentation[0].lesson.questions.question_list
                    preferential = models.Preferential.objects.get(
                        Q(user_id=self.request.user.id) & Q(lesson_id=presentation[0].lesson.id))
                    score_balance = preferential.score_balance
                    score_balance_dict = {}
                    for key in range(1, len(score_balance) + 1):
                        score_balance_dict[key] = score_balance[key - 1]
                    score_instance = models.Score.objects.filter(
                        Q(presentation_id=self.kwargs['presentation_id']) & Q(
                            score_giver__user_id=self.request.user.id))
                    # Checking the presence of scores with the desired specifications (for editing)
                    # Score editing mode
                    if score_instance.exists():
                        args = {
                            'presentation': presentation[0],
                            'questions': questions,
                            'score_balances': score_balance_dict,
                            'score_list': score_instance[0].score_list,
                        }
                        return render(self.request, 'score/register_score.html', args)
                    # Score Register mode
                    else:
                        args = {
                            'presentation': presentation[0],
                            'questions': questions,
                            'score_balances': score_balance_dict,
                        }
                        return render(self.request, 'score/register_score.html', args)
                else:
                    args = {
                        'message': 'ارائه یافت نشد.',
                        'url': reverse('score:presentations', kwargs={'group_id': self.kwargs['group_id']}),
                    }
                    return render(self.request, 'score/message_redirect.html', args)
            else:
                args = {
                    'message': 'شما در زمان این ارائه غایب بودید و مجاز به امتیاز دهی نمی باشید.',
                    'url': reverse('score:presentations', kwargs={'group_id': self.kwargs['group_id']}),
                }
                return render(self.request, 'score/message_redirect.html', args)
        else:
            args = {
                'message': 'شما عضو این درس نمی باشید.',
                'url': reverse('score:lessons'),
            }
            return render(self.request, 'score/message_redirect.html', args)

    def post(self, *args, **kwargs):
        posted_data = self.request.POST
        # Build a list of points received from request.POST
        score_text = {key: value for key, value in posted_data.items() if 'question' in key}.values()
        score_list = [int(i) for i in list(score_text)]
        '''
        Considering that the score_giver field located in the score model refers to Preferential
        score_giver__user_id was used in the query.
        '''
        score_instance = models.Score.objects.filter(
            Q(presentation_id=self.kwargs['presentation_id']) & Q(score_giver__user_id=self.request.user.id))
        lesson = models.Presentation.objects.filter(id=self.kwargs['presentation_id'])[0].lesson
        posted_data_reformatted = {
            "csrfmiddlewaretoken": posted_data['csrfmiddlewaretoken'],
            "presentation": self.kwargs['presentation_id'],
            "score_giver": models.Preferential.objects.get(Q(user_id=self.request.user.id) & Q(lesson_id=lesson.id)).id,
            "score_list": score_list,
        }
        # If there is a score instance, it edits it. Otherwise, it creates a new instance
        if score_instance.exists():
            form = forms.ScoreScoreAdd(posted_data_reformatted, instance=score_instance[0])
        else:
            form = forms.ScoreScoreAdd(posted_data_reformatted)
        if form.is_valid():
            form.save()
            args = {
                'message': 'اطلاعات ذخیره شد.',
                'url': reverse('score:score_chart'),
            }
            return render(self.request, 'score/message_redirect.html', args)
        presentation = models.Presentation.objects.filter(id=self.kwargs['presentation_id'])
        questions = presentation[0].lesson.questions.question_list
        preferential = models.Preferential.objects.get(
            Q(user_id=self.request.user.id) & Q(lesson_id=presentation[0].lesson.id))
        score_balance = preferential.score_balance
        score_balance_dict = {}
        for key in range(1, len(score_balance) + 1):
            score_balance_dict[key] = score_balance[key - 1]
        args = {
            'presentation': presentation[0],
            'questions': questions,
            'score_balances': score_balance_dict,
            'score_list': score_list,
            'form': form,
        }
        return render(self.request, 'score/register_score.html', args)


def save_lessons_and_preferentials(request):
    lessons = models.Lesson.objects.all()
    for lesson in lessons:
        lesson.save()
        lesson_users = User.objects.filter(groups__id=lesson.group.id)
        if lesson_users:
            lesson_preferentials = lesson.preferential_lesson.all()
            for lesson_user in lesson_users:
                preferential = lesson_preferentials.filter(user_id=lesson_user.id)
                if preferential:
                    preferential = preferential[0]
                else:
                    # Creating a Preferential instance with the highest score of this course for user
                    # who do not have a Preferential instance of this lesson
                    preferential = models.Preferential(user=lesson_user, lesson=lesson,
                                                       score_balance=lesson.initial_score)
                preferential.save()
        presentations = models.Presentation.objects.filter(lesson_id=lesson.id)
        for presentation in presentations:
            scores = presentation.score_presentation.all()
            presentation.score = 0
            for score in scores:
                for i in score.score_list:
                    presentation.score += i
            presentation.save()
    return HttpResponse('Everything was saved.')
