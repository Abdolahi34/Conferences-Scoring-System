from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group

from score import models


# Automatic creation of Lesson instance after creation of each group
@receiver(post_save, sender=Group)
def run_after_save_group_model(sender, instance, created, **kwargs):
    lesson = models.Lesson.objects.filter(group_id=instance.id)
    if not lesson:
        lesson = models.Lesson(group=instance)
        lesson.save()
