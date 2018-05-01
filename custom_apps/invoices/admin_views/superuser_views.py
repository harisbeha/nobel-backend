from django.contrib.admin import register, ModelAdmin
from import_export.admin import ImportExportActionModelAdmin

from ..models import *


# all the views in this file should be visible only to the superuser
class SuperuserModelAdmin(ImportExportActionModelAdmin):
    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return False


@register(Building)
class BuildingAdmin(SuperuserModelAdmin):
    pass


@register(RegionalAdmin)
class RegionalManagerAdmin(SuperuserModelAdmin):
    pass


@register(VendorSettings)
class VendorSettingsAdmin(SuperuserModelAdmin):
    pass


@register(Vendor)
class VendorAdmin(SuperuserModelAdmin):
    pass


@register(WorkOrder)
class WorkOrderAdmin(SuperuserModelAdmin):
    raw_id_fields = ("building",)


@register(WorkVisit)
class WorkVisitAdmin(SuperuserModelAdmin):
    pass


@register(SafetyReport)
class SafetyReportAdmin(SuperuserModelAdmin):
    pass


@register(DiscrepancyReport)
class DiscrepancyReportAdmin(SuperuserModelAdmin):
    pass


@register(Invoice)
class InvoiceAdmin(SuperuserModelAdmin):
    pass
