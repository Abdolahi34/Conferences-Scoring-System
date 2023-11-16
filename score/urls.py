from django.urls import path

from score import views

app_name = 'score'
urlpatterns = [
    path('', views.score_chart, name='score_chart'),  # TODO create score chart
    path('lessons/', views.lessons_list, name='lessons'),
    path('lessons/<int:lesson_id>/', views.presentation_list, name='presentations'),
    path('lessons/<int:lesson_id>/<int:presentation_id>/', views.RegisterScore.as_view(), name='register_score'),
]
