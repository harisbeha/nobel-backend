from django.contrib.admin import register, ModelAdmin
from import_export.admin import ImportExportActionModelAdmin

from ..models import *


# all the views in this file should be visible only to the superuser
class SuperuserModelAdmin(ImportExportActionModelAdmin):
    exclude = ['address_info_storage']
    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return False


@register(Building)
class BuildingAdmin(SuperuserModelAdmin):
    list_display = ['address', 'type']


@register(RegionalAdmin)
class RegionalManagerAdmin(SuperuserModelAdmin):
    list_display = ['name', 'system_user']


@register(VendorSettings)
class VendorSettingsAdmin(SuperuserModelAdmin):
    list_display = ['const_a', 'const_b', 'vendor']


@register(Vendor)
class VendorAdmin(SuperuserModelAdmin):
    list_display = ['name', 'address', 'system_user']


@register(WorkOrder)
class WorkOrderAdmin(SuperuserModelAdmin):
    list_display = ['vendor', 'invoice', 'building', 'storm_name']
    raw_id_fields = ("building",)


@register(WorkVisit)
class WorkVisitAdmin(SuperuserModelAdmin):
    list_display = ['work_order', 'response_time_start', 'response_time_end']


@register(SafetyReport)
class SafetyReportAdmin(SuperuserModelAdmin):
    list_display = ['work_order', 'safe_to_open']


@register(DiscrepancyReport)
class DiscrepancyReportAdmin(SuperuserModelAdmin):
    list_display = ['work_order', 'author', 'message']


@register(Invoice)
class InvoiceAdmin(SuperuserModelAdmin):
    list_display = ['vendor', 'remission_address']
