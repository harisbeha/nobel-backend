from celery.task import task

from custom_apps.data_ingestion.bq import fetch_for_accumulation_zip
import json

@task
def ingest_snowfall_data(zipcode, start, end, safety_report=None, work_order=None):
    print('triggered')
    #values = fetch_for_accumulation_zip(zipcode, start, end)
    values = _query_accumulation_data(zipcode, start, end)
    print('result')
    print(json.dumps(values))
    if values != None:
        if safety_report:
            safety_report.verify_weather = json.dumps(values)
            safety_report.save()
        if work_order:
            work_order.verify_weather = json.dumps(values)
            safety_report.save()

