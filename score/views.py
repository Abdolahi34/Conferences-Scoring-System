from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
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
    lessons = Group.objects.all()
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
def presentations_list(request, lesson_id):
    # Examining student membership in the course
    if User.objects.filter(Q(groups__id=lesson_id) & Q(id=request.user.id)).exists():
        presentations = models.Presentation.objects.filter(Q(lesson_id=lesson_id) & Q(is_active=True))
        # Checking the existence and activeness of the presentation
        if presentations.exists():
            lesson = Group.objects.get(id=lesson_id)
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
        # Examining student membership in the course
        if User.objects.filter(Q(groups__id=self.kwargs['lesson_id']) & Q(id=self.request.user.id)).exists():
            presentation = models.Presentation.objects.filter(Q(id=self.kwargs['presentation_id']) & Q(is_active=True))
            # Checking the existence and activeness of the presentation
            if presentation.exists():
                questions = presentation[0].lesson.questions.question_list
                score_instance = models.Score.objects.filter(
                    Q(presentation_id=self.kwargs['presentation_id']) & Q(score_giver__user_id=self.request.user.id))
                # Checking the presence of scores with the desired specifications (for editing)
                # Score editing mode
                if score_instance.exists():
                    args = {
                        'presentation': presentation[0],
                        'questions': questions,
                        'score_list': score_instance[0].score_list,
                    }
                    return render(self.request, 'score/register_score.html', args)
                # Score Register mode
                else:
                    args = {
                        'presentation': presentation[0],
                        'questions': questions,
                    }
                    return render(self.request, 'score/register_score.html', args)
            else:
                args = {
                    'message': 'ارائه یافت نشد.',
                    'url': reverse('score:presentations', kwargs={'lesson_id': self.kwargs['lesson_id']}),
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
        posted_data_reformatted = {
            "csrfmiddlewaretoken": posted_data['csrfmiddlewaretoken'],
            "presentation": self.kwargs['presentation_id'],
            "score_giver": models.Preferential.objects.get(user_id=self.request.user.id).id,
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
        args = {
            'presentation': presentation[0],
            'questions': questions,
            'score_list': score_list,
            'form': form,
        }
        return render(self.request, 'score/register_score.html', args)
