from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class ExtendUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    finishedTutorial = models.BooleanField(default=False)
    def __str__(self):
        return self.user.username