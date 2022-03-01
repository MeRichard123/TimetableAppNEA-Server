from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import ExtendUser

@receiver(post_save, sender=User)
def create_extended_user(sender, instance, created, **kwargs):
    if created:
        ExtendUser.objects.create(user=instance)
