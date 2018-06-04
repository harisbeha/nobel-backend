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


@receiver(post_save, sender=SafetyReport)
def create_work_orders(sender, instance, created, **kwargs):
    import random
    from custom_apps.invoices.models import WorkOrder
    work_order_code = 'T'.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVXYZ') for i in range(6))
    WorkOrder.objects.get_or_create(building=instance.building, invoice=instance.invoice,
                                    storm_name=instance.invoice.storm_name,
                                    service_provider=instance.building.service_provider,
                                    work_order_code=work_order_code)

@receiver(post_save, sender=SafetyReport)
def email_safety_report(sender, instance, created, **kwargs):
    import random
    from custom_apps.invoices.models import WorkOrder