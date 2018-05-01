from import_export import resources
from .models import *

"""
Usage

from custom_apps.invoices.resources import WorkOrderResource
dataset = WorkOrderResource().export()
print dataset.csv 
result
"""

WO
    flag_safe = Field()
    flag_visitsdocumented = Field()
    flag_weatherready = Field()
    flag_failure = Field()
    flag_hasdiscrepancies = Field()
    flag_hasdiscrepanciesfailure = Field()
    flag_completed = Field()


WorkVisit    provided_deicing = Field()

    provided_deicing
    provided_plowing


class AddressMetadataStorageMixinResource(resources.ModelResource):
    class Meta:
        model = AddressMetadataStorageMixin
        fields = '__all__'


class VendorSettingsResource(resources.ModelResource):
    class Meta:
        model = VendorSettings
        fields = '__all__'


class VendorResource(resources.ModelResource):
    class Meta:
        model = Vendor
        fields = '__all__'


class RegionalAdminResource(resources.ModelResource):
    class Meta:
        model = RegionalAdmin
        fields = '__all__'


class InvoiceResource(resources.ModelResource):
    class Meta:
        model = Invoice
        fields = '__all__'


class BuildingResource(resources.ModelResource):
    class Meta:
        model = Building
        fields = '__all__'


class WorkOrderResource(resources.ModelResource):
    flag_safe = Field()
    flag_visitsdocumented = Field()
    flag_weatherready = Field()
    flag_failure = Field()
    flag_hasdiscrepancies = Field()
    flag_hasdiscrepanciesfailure = Field()
    flag_completed = Field()

    class Meta:
        model = WorkOrder
        fields = (flag_safe, flag_visitsdocumented, )

    def dehydrate_flag_safe(self, obj):
        return '%s' % ('true' if not obj.flag_safe else 'false')

    def dehydrate_flag_visitsdocumented(self, obj):
        return '%s' % ('true' if not obj.flag_visitsdocumented else 'false')

    def dehydrate_flag_weatherready(self, obj):
        return '%s' % ('true' if not obj.flag_weatherready else 'false')

    def dehydrate_flag_failure(self, obj):
        return '%s' % ('true' if not obj.flag_failure else 'false')

    def dehydrate_flag_hasdiscrepancies(self, obj):
        return '%s' % ('true' if not obj.flag_hasdiscrepancies else 'false')

    def dehydrate_flag_hasdiscrepanciesfailure(self, obj):
        return '%s' % ('true' if not obj.flag_hasdiscrepanciesfailure else 'false')

    def dehydrate_flag_completed(self, obj):
        return '%s' % ('true' if not obj.flag_completed else 'false')

class WorkVisitResource(resources.ModelResource):
    provided_deicing = Field()
    provided_deicing = Field()

    class Meta:
        model = WorkVisit
        fields = '__all__'


class SafetyReportResource(resources.ModelResource):
    safe_to_open = Field()

    class Meta:
        model = SafetyReport
        fields = '__all__'

    def dehydrate_safe_to_open(self, obj):
        return '%s' % ('true' if not obj.safe_to_open else 'false')


class DiscrepancyReportResource(resources.ModelResource):
    class Meta:
        model = DiscrepancyReport
        fields = '__all__'


class RegionalAdminProxyNWAResource(resources.ModelResource):
    class Meta:
        model = RegionalAdminProxyNWA
        fields = '__all__'


class WorkOrderProxyNWAResource(resources.ModelResource):
    class Meta:
        model = WorkOrderProxyNWA
        fields = '__all__'


class VendorProxyCBREResource(resources.ModelResource):
    class Meta:
        model = VendorProxyCBRE
        fields = '__all__'


class WorkOrderProxyCBREResource(resources.ModelResource):
    class Meta:
        model = WorkOrderProxyCBRE
        fields = '__all__'


class WorkOrderProxyVendorResource(resources.ModelResource):
    class Meta:
        model = WorkOrderProxyVendor
        fields = '__all__'
