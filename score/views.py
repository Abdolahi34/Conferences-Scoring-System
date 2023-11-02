from django.shortcuts import render, HttpResponse, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.views import View
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.core.exceptions import PermissionDenied

from score import models


@login_required
def lessons_list(request):
    lessons = Group.objects.all()
    args = {'lessons': lessons}
    return render(request, 'score/lessons_list.html', args)


@login_required
def users_list(request, lesson_id):
    # بررسی عضویت دانشجو در درس
    if User.objects.filter(Q(groups__id=lesson_id) & Q(id=request.user.id)).exists():
        lesson = Group.objects.get(id=lesson_id)
        users = User.objects.filter(groups__id=lesson_id)
        args = {'lesson': lesson, 'users': users}
        return render(request, 'score/users_list.html', args)
    else:
        raise PermissionDenied('a')

