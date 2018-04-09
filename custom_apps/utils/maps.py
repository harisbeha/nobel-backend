import googleplaces
from django.conf import settings


def formalize_address(addr):
    cl = googleplaces.GooglePlaces(settings.GOOGLE_PLACES_API_KEY)
    places = cl.text_search(addr).places
    if places:
        for place in places:
            place.get_details()
            fmt_addr = place.formatted_address
            if fmt_addr:
                deconstructed = {i['types'][0]: i.get('long_name', i.get('short_name', None))
                                 for i in
                                 place.details['address_components']}
                return fmt_addr, deconstructed
    return None, None
