import json

from django.conf import settings
from google.cloud.bigquery import Client, ScalarQueryParameter, QueryJobConfig
import random
import time
import datetime
from custom_apps.utils import redis_client
from datetime import timezone
_client = None


def _get_client():
    global _client
    if not _client:
        _client = Client.from_service_account_json(settings.GOOGLE_CLOUD_JSON)
    return _client


ACCUMULATION_QUERY = '''
SELECT
  logical_or(precipitationType = 6) AS has_ice,
  sum(total) as snowfall
  FROM
    dev.cst_snowfall_data
  WHERE
    zipCode = @zipcode
    AND startTime <= @startdate
    AND endTime >= @enddate
  LIMIT
   1200
'''


def make_accumulation_key(zipcode, start, end):
    return 'accumulation-%s-%s-%s' % (zipcode, start, end)


# TODO: NOTHING TO DO - STUFF IS HARDCODED HERE - NEVER FORGET
def _query_accumulation_data(zipcode, start, end, safety_report=None, work_order=None):
    bq = _get_client()
    start = datetime.datetime.strftime(start, "%F %H:%M") 
    ends = datetime.datetime.strftime(end, "%F %H:%M")
    query_params = [
        ScalarQueryParameter('zipcode', 'INT64', int(zipcode)),
        ScalarQueryParameter('startdate', 'TIMESTAMP', start),
        ScalarQueryParameter('enddate', 'TIMESTAMP', end),
    ]
    job_config = QueryJobConfig()
    job_config.query_parameters = query_params
    query = bq.query(ACCUMULATION_QUERY, job_config=job_config)
    result = query.result()
    print(result)
    r = dict(list(result)[0].items())
    return r


def query_for_accumulation_zip(zipcode, start, end, safety_report=None, work_order=None):
    cache_key = make_accumulation_key(zipcode, start, end)
    cached_result = redis_client.get_key(cache_key)
    if cached_result is not None:
        try:
            return json.loads(cached_result)
        except Exception as e:
            print(e)
    from .tasks import ingest_snowfall_data
    if safety_report:
        ingest_snowfall_data.delay(zipcode, start, end, safety_report)
    if work_order:
        ingest_snowfall_data.delay(zipcode, start, end, work_order)


def fetch_for_accumulation_zip(zipcode, start, end, safety_report=None, work_order=None):
    cache_key = make_accumulation_key(zipcode, start, end)
    fetch_key = 'fetch-%s' % cache_key
    if redis_client.get_key(fetch_key) is not None:
        redis_client.set_key(fetch_key, '1', 3600)
        r = _query_accumulation_data(zipcode, start, end)
        redis_client.set_key(cache_key, json.dumps(r))
        redis_client.del_key(fetch_key)

# print query_for_accumulation_zip(6051, parse('2018-04-02 03:00:00.000 UTC'), parse('2018-04-02 14:00:00.000 UTC'))
