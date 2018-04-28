from django.contrib.admin import register, ModelAdmin, StackedInline

from custom_apps.invoices.admin_views.common import AppendOnlyMixin
from custom_apps.invoices.models import SafetyReport, WorkVisit, DiscrepancyReport
from ..models import WorkOrderProxyVendor
from ..enums import Group


# all the views in this file should be visible only to vendor
class VendorModelAdmin(ModelAdmin):
    def has_module_permission(self, request):
        if request.user.groups.filter(name=Group.VENDOR.value).count() > 0:
            return True
        return False


# this is the inline for adding safety reports to a workorder
class SafetyReportInline(StackedInline, AppendOnlyMixin):
    model = SafetyReport

    # TODO: set parent's flag_safe = True if obj.safe = True

    def has_add_permission(self, request):
        # TODO: disable adds when parent's flag_safe = True
        return True


# this is the inline for adding work visits to a workorder
class WorkVisitInline(StackedInline, AppendOnlyMixin):
    model = WorkVisit

    def has_add_permission(self, request):
        # TODO: disable adds when parent's flag_visitsdocumented = True
        return True


# this is the inline for adding discrepancy reports to a workorder
class DiscrepancyReportInline(StackedInline, AppendOnlyMixin):
    model = DiscrepancyReport

    # TODO: set authorship automatically
    # TODO: set parent's flag_hasdiscrepancies = None and send email on creation

    def has_add_permission(self, request):
        # TODO: disable adds when flag_hasdiscrepancies != True or flag_hasdiscrepanciesfailure = True
        return True


# this is the admin for creating and editing workorders
@register(WorkOrderProxyVendor)
class VendorCreatesWorkOrders(VendorModelAdmin):
    # TODO: disallow specifying an invoice during object creation
    # TODO: the vendor should automatically be the user's vendor during object creation
    # TODO: widget for searching for buildings during object creation
    # TODO: add to weather processing queue on creation
    # TODO: sidebar filter for flag_hasdiscrepancies = True && flag_hasdiscrepanciesfailure = False
    # TODO: action to mark flag_visitsdocumented = True

    inlines = [SafetyReportInline, WorkVisitInline, DiscrepancyReportInline]

    def get_queryset(self, request):
        qs = super(VendorCreatesWorkOrders, self).get_queryset(request)
        # TODO: filter by the current user's vendor
        return qs

    def get_readonly_fields(self, request, obj=None):
        return self.model._meta.fields

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.flag_completed:
            return False
        return True  # TODO: is this the right thing to do?
