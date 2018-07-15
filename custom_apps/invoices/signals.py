from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
# replace with shortcut get grab auth model
from .models import *
from custom_apps.data_ingestion.bq import query_for_accumulation_zip

def connect_state_workflow():
    pass

@receiver(pre_save, sender=User)
def set_email_to_username(sender, instance, **kwargs):
    instance.email = instance.username


@receiver(post_save, sender=SafetyVisit)
def create_work_orders(sender, instance, created, **kwargs):
    import random
    from custom_apps.invoices.models import WorkOrder



    # WorkVisit.objects.get_or_create(building=instance.building, invoice=instance.invoice,
    #                                 service_date=instance.invoice.storm_date,
    #                                 storm_name=instance.invoice.storm_name,
    #                                 service_provider=instance.building.service_provider,
    #                                 work_order_code=work_order_code)

@receiver(post_save, sender=WorkVisit)
def ingest_workorder_data(sender, instance, created, **kwargs):
    from custom_apps.data_ingestion.bq import query_for_accumulation_zip
    if created:
        query_for_accumulation_zip(instance.work_order.building.zip_code, instance.service_date,
                                   instance.service_date, work_order=instance)
        work_order = instance.work_order
        if work_order.salt_delta > 0.0:
            work_order.is_discrepant = True
        if work_order.plow_delta > 0.0:
            work_order.is_discrepant = True
        work_order.save()

@receiver(post_save, sender=SafetyReport)
def ingest_safetyreport_data(sender, instance, created, **kwargs):
    from custom_apps.data_ingestion.bq import query_for_accumulation_zip
    if created:
        query_for_accumulation_zip(instance.building.zip_code, instance.inspection_date, instance.inspection_date,
                                   safety_report=instance)

