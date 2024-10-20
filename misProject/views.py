from django.shortcuts import render, reverse


def main_page(request):
    return render(request, 'misProject/force_redirect.html', {'url': reverse('score:lessons')})

