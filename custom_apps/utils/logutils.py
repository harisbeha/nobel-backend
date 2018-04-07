import json
import logging
import re
from collections import OrderedDict
from logging import Formatter

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django_requestlogging.logging_filters import RequestFilter
from log_request_id import local

MAX_BODY_LENGTH = 50000  # log no more than 3k bytes of content
request_logger = logging.getLogger('django.request')
regex_header = re.compile(r'^(HTTP_.+|CONTENT_TYPE|CONTENT_LENGTH)$')


def deep_merge(base, extra):
    """Deeply two dictionaries, overriding existing keys in the base.

    :param base: The base dictionary which will be merged into.
    :param extra: The dictionary to merge into the base. Keys from this
        dictionary will take precedence.
    """
    for key in extra:
        # If the key represents a dict on both given dicts, merge the sub-dicts
        if key in base and isinstance(base[key], dict) \
                and isinstance(extra[key], dict):
            deep_merge(base[key], extra[key])
            continue

        # Otherwise, set the key on the base to be the value of the extra.
        base[key] = extra[key]


class SafeJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        try:
            return super(SafeJSONEncoder, self).default(o)
        except Exception as e:
            return


class LoggingMiddleware(object):
    def process_request(self, request):
        request_headers = {}
        for header in request.META:
            if regex_header.match(header):
                key = header.lower().replace('_', '-')
                if key.startswith('http-'):
                    key = key.replace('http-', '', 1)
                request_headers[key] = request.META[header]
        request_logger.info('Processing request', extra={'context': {
            'http': {
                'request': {
                    'headers': request_headers,
                    'method': request.method,
                    'path': request.get_full_path(),
                    'content': request.body[0:3000],
                }
            }
        }})

    def process_response(self, request, response):
        try:
            response_length = len(response.content)
        except AttributeError:
            response_length = '__stream__'
        except:
            response_length = None
        try:
            content_summary = response.content[0:1000]
        except AttributeError:
            content_summary = '__stream__'
        except:
            response_length = None

        request_logger.info('Processing response', extra={'context': {
            'http': {
                'response': {
                    'status': response.status_code,
                    'reason_phrase': response.reason_phrase,
                    'url': getattr(response, 'url', '-'),
                    'length': response_length,
                    'headers': {k: v[1] for k, v in response._headers.iteritems()},
                    'content': content_summary
                }
            }}})
        return response


class LoggingFilter(RequestFilter):
    def filter(self, record):
        super(LoggingFilter, self).filter(record)
        record.request_id = getattr(local, 'request_id', '-')
        return True


class JSONFormatter(Formatter):
    def format(self, record):
        values = record.__dict__
        # Strip entries with value "-" or in blacklist (LOGGING_EXCLUDE_FIELDS)
        json_record = {k: v for (k, v) in
                       filter(None,
                              [
                                  i
                                  if ((i[1] != '-' and i[1]) and i[0] not in settings.LOGGING_EXCLUDE_FIELDS)
                                  else None
                                  for i in values.items()
                              ]
                              )
                       }
        ordered = OrderedDict()
        if 'msg' in json_record and 'args' in json_record:
            try:
                json_record['formatted_msg'] = json_record['msg'] % json_record['args']
            except TypeError:
                pass

        configs = {
            'python': ['module', 'funcName', 'filename', 'levelno', 'processName', 'lineno', 'thread', 'created',
                       'threadName', 'msecs', 'pathname', 'relativeCreated', 'process'],
            'http': ['request_id', 'request_method', 'path_info', 'remote_addr', 'http_user_agent', 'server_protocol', ]

        }
        for i in ['name', 'formatted_msg', 'msg', 'levelname', 'request_method', 'path_info', 'args']:
            if i in json_record:
                ordered[i] = json_record[i]
                del json_record[i]

        for name, config in configs.iteritems():
            fields = config
            obj = OrderedDict()
            for f in fields:
                if f in json_record:
                    obj[f] = json_record[f]
                    del json_record[f]
            deep_merge(ordered, {name: obj})

        for i in json_record.iterkeys():
            ordered[i] = json_record[i]

        copy = OrderedDict()
        for k, v in ordered.iteritems():
            try:
                json.dumps(v)
            except:
                # request_logger.info('Failed to serialize %s' % k)
                del ordered[k]
                continue
            if not isinstance(v, OrderedDict):
                copy[k] = v
                del ordered[k]
            elif isinstance(v, OrderedDict) and not len(v):
                del ordered[k]

        copy.update(ordered)

        return json.dumps(copy, cls=SafeJSONEncoder)
