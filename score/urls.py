from django.urls import path
from django.views.generic.base import RedirectView

from score import views

app_name = 'score'
urlpatterns = [
    path('', RedirectView.as_view(url='lessons/'), name='score_chart'),  # TODO create score chart
    path('lessons/', views.lessons_list, name='lessons'),
    path('save-lessons/', views.save_lessons, name='save_lessons'),
    path('lessons/<int:group_id>/', views.presentations_list, name='presentations'),
    path('lessons/<int:group_id>/<int:presentation_id>/', views.RegisterScore.as_view(), name='register_score'),
]
