from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group, User

from score import models


# Automatic creation of Preferential instance after creation of each user
@receiver(post_save, sender=User)
def run_after_save_user_model(sender, instance, created, **kwargs):
    pass  # todo


# Automatic creation of Lesson instance after creation of each group
@receiver(post_save, sender=Group)
def run_after_save_group_model(sender, instance, created, **kwargs):
    if created:
        lesson = models.Lesson(group=instance)
        lesson.save()
