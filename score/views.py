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


@method_decorator(login_required, name="dispatch")
class RegisterScore(View):
    def get(self, *args, **kwargs):
        # بررسی عضویت دانشجو در درس
        if User.objects.filter(Q(groups__id=self.kwargs['lesson_id']) & Q(id=self.request.user.id)).exists():
            # آیا یوزر فعلی به یوزری که id آن در url وارد شده امتیاز داده است؟
            if models.Point.objects.filter(Q(presentation__lesson_id=self.kwargs['lesson_id']) & Q(
                    presentation__presenter_id=self.kwargs['user_id']) & Q(point_giver_id=self.request.user.id)):
                user = User.objects.get(id=self.kwargs["user_id"])
                return HttpResponse(
                    f'<h3 dir="rtl">به هر ارائه تنها <span style="color: red">یک مرتبه</span> میتوان امتیاز داد.<br>شما به {user.first_name} {user.last_name} رای داده اید.</h3>')
            else:
                presentation = get_object_or_404(models.Presentation, Q(lesson_id=self.kwargs['lesson_id']) & Q(
                    presenter_id=self.kwargs['user_id']))
                questions = presentation.questions
                args = {'presentation': presentation, 'questions': questions}
                return render(self.request, 'score/register_point.html', args)
        else:
            raise PermissionDenied()

    def post(self, *args, **kwargs):
        pass
