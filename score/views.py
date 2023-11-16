from django.shortcuts import render, HttpResponse, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.views import View
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.core.exceptions import PermissionDenied

from score import models


# TODO نمودار ارائه همه دروس
def score_chart(request):
    pass


@login_required
def lessons_list(request):
    lessons = Group.objects.all()
    args = {'lessons': lessons}
    return render(request, 'score/lessons_list.html', args)


@login_required
    # بررسی عضویت دانشجو در درس
def presentation_list(request, lesson_id):
    if User.objects.filter(Q(groups__id=lesson_id) & Q(id=request.user.id)).exists():
        lesson = Group.objects.get(id=lesson_id)
        users = User.objects.filter(groups__id=lesson_id)
        args = {'lesson': lesson, 'users': users}
        return render(request, 'score/users_list.html', args)
    else:
        raise PermissionDenied('a')


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
