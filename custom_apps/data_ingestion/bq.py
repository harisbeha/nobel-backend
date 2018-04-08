from django.conf import settings
from google.cloud.bigquery import Client, ScalarQueryParameter, QueryJobConfig

_client = None


def _get_client():
    global _client
    if not _client:
        _client = Client.from_service_account_json(settings.GOOGLE_CLOUD_JSON)
    return _client


ACCUMULATION_QUERY = '''SELECT SUM(total_accumulation) AS total
FROM (
  SELECT total_accumulation
  FROM
    dev.cst_snowfall_data
  WHERE
    precip_type = 'Snow'
    AND `zipcode` = @zipcode
    AND `end` <= @enddate
    AND `start` >= @startdate
  LIMIT
  1000)'''


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
    return list(result)[0].values()[0]

# print query_for_accumulation_zip(6051, parse('2018-04-02 03:00:00.000 UTC'), parse('2018-04-02 14:00:00.000 UTC'))
