from import_export import resources
from .models import *

"""
Usage

from custom_apps.invoices.resources import WorkOrderResource
dataset = WorkOrderResource().export()
print dataset.csv 
result
"""


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
    class Meta:
        model = WorkOrder
        fields = '__all__'


class WorkVisitResource(resources.ModelResource):
    class Meta:
        model = WorkVisit
        fields = '__all__'


class SafetyReportResource(resources.ModelResource):
    class Meta:
        model = SafetyReport
        fields = '__all__'


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
