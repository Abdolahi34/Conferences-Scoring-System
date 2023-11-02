from django.urls import path

from score import views

app_name = 'score'
urlpatterns = [
    path('lessons/', views.lessons_list, name='score_lessons'),
    path('lessons/', views.lessons_list, name='lessons'),
    path('lessons/<int:lesson_id>/', views.users_list, name='users'),
]
