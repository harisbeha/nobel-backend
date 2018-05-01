from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
# replace with shortcut get grab auth model

from .models import *


def connect_state_workflow():
    pass

@receiver(pre_save, sender=User)
def set_email_to_username(sender, instance, **kwargs):
    instance.email = instance.username