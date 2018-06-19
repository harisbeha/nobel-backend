from ..models import Building, Vendor

def get_locations_by_system_user(user=None, provider=None):
    # vendor = Vendor.objects.filter(system_user__email='VENDOR@VENDOR.com')[0]
    #print(provider)
    if provider:
        locations = Building.objects.filter(service_provider=provider)
    else:
        vend = Vendor.objects.get(system_user=user)
        locations = Building.objects.filter(service_provider=vend)
    return locations