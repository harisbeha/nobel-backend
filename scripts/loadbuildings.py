from custom_apps.invoices.models import Building, Vendor, Invoice, WorkOrder, RegionalAdmin
from django.contrib.auth.models import User


def create_buildings(json_data):
    for row in json_data:
        vendor_name = row['vendor']
        vendor_email = 'vendor-user@{vendor}.com'.format(vendor=vendor_name.lower())
        user, user_created = User.objects.get_or_create(email=vendor_email, username=vendor_email)
        vendor, vendor_created = Vendor.objects.get_or_create(system_user=user, name=vendor_name, address='temp',
                                                              region=RegionalAdmin.objects.all()[0])
        if user_created:
            user.set_password('P@ssw0rd')
        new_deicing_rate = row['deicing_rate'].replace('$', '').replace(',', '').replace(' per hour', '')
        if new_deicing_rate == '':
            new_deicing_rate = 0.0
        new_plow_rate = row['plow_rate'].replace('$', '').replace(',', '').replace(' per hour', '')
        if new_plow_rate == '':
            new_plow_rate = 0.0

        new_plow_tax = row['plow_tax'].replace('$', '').replace(',', '').replace(' per hour', '')
        if new_plow_tax == '':
            new_plow_tax = 0.0

        new_deice_tax = row['plow_tax'].replace('$', '').replace(',', '').replace(' per hour', '')
        if new_plow_tax == '':
            new_plow_tax = 0.0
        address = '{0}, {1}, {2} {3}'.format(row['address'], row['city'], row['state'], row['zip'])

        Building.objects.get_or_create(service_provider=vendor, address=address, plow_rate=new_plow_rate,
                                       deice_rate=new_deicing_rate, type=1, deice_tax=0, plow_tax=0,
                                       building_code=row['building_id'])
