from django.urls import path
from django.views.generic.base import RedirectView

from score import views

app_name = 'score'
urlpatterns = [
    path('', RedirectView.as_view(url='lessons/'), name='score_chart'),  # TODO create score table
    path('lessons/', views.lessons_list, name='lessons'),
    path('lessons/<int:group_id>/', views.presentations_list, name='presentations'),
    path('lessons/<int:group_id>/<int:presentation_id>/', views.RegisterScore.as_view(), name='register_score'),
    path('save/', views.save_lessons_and_preferentials, name='save_lessons_and_preferentials'),
]
