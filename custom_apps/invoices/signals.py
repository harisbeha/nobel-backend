from django.db.models.signals import pre_save, post_save

from .models import *


def job_creation_tracker(sender, instance, *args, **kwargs):
    if instance.state == ReportState.CREATED.value:
        # test all the fields to make sure they're ready for safety review
        # ...none right now
        instance.state = ReportState.INITIALIZED.value


def vendor_tracker(sender, instance, created, **kwargs):
    if created:
        Invoice.objects.create(vendor=instance, remission_address=None, invoice_number=None)


def connect_state_workflow():
    post_save.connect(vendor_tracker, Vendor)
    pre_save.connect(job_creation_tracker, Job)
