from django.urls import path

from score import views

app_name = 'score'
urlpatterns = [
    path('lessons/', views.lessons_list, name='score_lessons'),
]
