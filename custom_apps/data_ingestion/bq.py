from django.conf import settings
from google.cloud.bigquery import Client, ScalarQueryParameter, QueryJobConfig

_client = None


def _get_client():
    global _client
    if not _client:
        _client = Client.from_service_account_json(settings.GOOGLE_CLOUD_JSON)
    return _client


ACCUMULATION_QUERY = '''
SELECT
  logical_or(precip_type LIKE '%Sleet%') AS has_ice,
  max(timestamp_diff(`end`, `start`, HOUR)) AS duration,
  sum(total_accumulation) as snowfall
  FROM
    dev.cst_snowfall_data
  WHERE
    precip_type = 'Snow'
    AND `zipcode` = @zipcode
    AND `end` <= @enddate
    AND `start` >= @startdate
  LIMIT
   1000 
'''


def query_for_accumulation_zip(zipcode, start, end):
    bq = _get_client()
    query_params = [
        ScalarQueryParameter('zipcode', 'INT64', zipcode),
        ScalarQueryParameter('startdate', 'TIMESTAMP', start),
        ScalarQueryParameter('enddate', 'TIMESTAMP', end),
    ]
    job_config = QueryJobConfig()
    job_config.query_parameters = query_params
    query = bq.query(ACCUMULATION_QUERY, job_config=job_config)
    result = query.result()
    return dict(list(result)[0].items())
