from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group


@login_required
def lessons_list(request):
    lessons = Group.objects.all()
    args = {'lessons': lessons}
    return render(request, 'score/lessons_list.html', args)

