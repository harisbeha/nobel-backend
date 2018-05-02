from celery.task import task

from custom_apps.data_ingestion.bq import fetch_for_accumulation_zip


@task
def ingest_snowfall_data(zipcode, start, end):
    fetch_for_accumulation_zip(zipcode, start, end)
