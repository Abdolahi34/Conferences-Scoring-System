from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group, User

from score import models


# Automatic creation of Preferential instance after creation of each user
@receiver(post_save, sender=User)
def run_after_save_user_model(sender, instance, created, **kwargs):
    user_groups = instance.groups.all()
    if user_groups:
        for user_group in user_groups:
            lesson = user_group.lesson_group.all()
            if lesson:
                lesson = lesson[0]
                initial_score_list = models.get_lesson_initial_score_list(user_group)
                models.set_preferential(lesson, initial_score_list)
            else:
                user_group.save()
                lesson = user_group.lesson_group.all()[0]
                initial_score_list = models.get_lesson_initial_score_list(user_group)
                models.set_preferential(lesson, initial_score_list)


# Automatic creation of Lesson instance after creation of each group
@receiver(post_save, sender=Group)
def run_after_save_group_model(sender, instance, created, **kwargs):
    if created:
        lesson = models.Lesson(group=instance)
        lesson.save()
