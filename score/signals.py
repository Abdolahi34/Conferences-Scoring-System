from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from score import models


# Automatic creation of Preferential instance after creation of each user
@receiver(post_save, sender=User)
def run_after_save_user_model(sender, instance, created, **kwargs):
    if not models.Preferential.objects.filter(user=instance).exists():
        preferential = models.Preferential(user=instance)
        preferential.save()
