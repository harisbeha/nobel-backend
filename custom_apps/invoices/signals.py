from django.db.models.signals import pre_save, post_save

from .models import *


def vendor_tracker(sender, instance, created, **kwargs):
    if created:
        Invoice.objects.create(vendor=instance, remission_address=None, invoice_number=None)


def connect_state_workflow():
    post_save.connect(vendor_tracker, Vendor)
