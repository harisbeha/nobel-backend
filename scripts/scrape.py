import os
import requests
import dateutil.parser
import time
import json
from HTMLParser import HTMLParser

# default: test key with access to new england
SCRAPE_API_KEY = os.environ.get('SCRAPE_API_KEY', 'cst_37mqLLFuPbUfQUYEwKNO2fir2B')

# default: 15 days
SCRAPE_SINCE = int(time.time()) - int(os.environ.get('SCRAPE_SINCE', 60*60*24*15))


def get_raw(since, api_key):
    r = requests.get('https://certifiedsnowfalltotals.com/api/storms', params={'publish_start': str(since)}, auth=(api_key, ''))
    for storm in r.json():
        for stormloc in storm['storm_locations']:
            out = dict()
            out.update(stormloc['data'])
            out.update(stormloc['location'])
            out['id'] = storm['id']
            out['start'] = dateutil.parser.parse(storm['start']).isoformat()
            out['end'] = dateutil.parser.parse(storm['end']).isoformat()
            out['location_id'] = stormloc['location']['id']
            out['narrative'] = strip_tags(out['narrative'])
            yield out


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return '. '.join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    fixed = s.get_data()
    for badchar in ' .':
        double = badchar*2
        while double in fixed:
            fixed = fixed.replace(double, badchar)
    return fixed.strip()


if __name__ == '__main__':
    for row in get_raw(SCRAPE_SINCE, SCRAPE_API_KEY):
        print json.dumps(row)
