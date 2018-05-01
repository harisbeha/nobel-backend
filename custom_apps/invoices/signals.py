from django.db.models.signals import receiver, post_save
from django.conf import settings

from custom_apps.data_ingestion.tasks import ingest_snowfall_data

from .models import *


def connect_state_workflow():
    pass


@receiver(post_save, sender=WorkOrder)
def compute_forecast_data(sender, instance, created, **kwargs):
    if created:
        zip_code = instance.building.address_field_storage['postal_code']

        # For demo only
        zip_code = settings.DEMO_SNOWFALL_ZIP
        ingest_snowfall_data(zip_code,
                             settings.DEMO_SNOWFALL_DATA_START,
                             settings.DEMO_SNOWFALL_DATA_END, instance)
