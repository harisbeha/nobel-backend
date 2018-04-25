from django.contrib.admin import register, ModelAdmin, StackedInline

from ..models import RegionalAdminProxyNWA, WorkOrderProxyNWA, WorkVisit, SafetyReport, DiscrepancyReport
from ..enums import Group
from .common import ReadOnlyMixin, AppendOnlyMixin


# all the views in this file should be visible only to nwa
class NWAModelAdmin(ModelAdmin):
    def has_module_permission(self, request):
        if request.user.groups.filter(name=Group.NWA.value).count() > 0:
            return True
        return False


# this is the admin for creating CBREs
@register(RegionalAdminProxyNWA)
class NWACreatesCBRE(NWAModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


# this is the inline to view workvisits within a workorder
class WorkVisitInline(StackedInline, ReadOnlyMixin):
    model = WorkVisit


# this is the inline to view safety reports within a workorder
class SafetyReportInline(StackedInline, ReadOnlyMixin):
    model = SafetyReport


# this is the inline for viewing and creating discrepancy reports in a workorder
class DiscrepancyReportInline(StackedInline, AppendOnlyMixin):
    model = DiscrepancyReport


# this is the inline for nwa to moderate work orders
@register(WorkOrderProxyNWA)
class NWAModeratesWorkOrders(NWAModelAdmin):
    # TODO: set flag_hasdiscrepancies = True and send email on discrepancy report - signal?
    # TODO: set authorship for discrepancy orders automatically
    # TODO: actions to mark flag_hasdiscrpancies = False or flag_hasdiscrepanciesfailure = True
    # TODO: evaluate has_change_permission vs get_readonly_fields for inlines

    inlines = [WorkVisitInline, SafetyReportInline, DiscrepancyReportInline]

    def get_readonly_fields(self, request, obj=None):
        return self.model._meta.fields

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def get_queryset(self, request):
        qs = super(NWAModeratesWorkOrders, self).get_queryset(request)
        return qs.filter(
            flag_weatherready=True,
            flag_visitsdocumented=True,
            flag_failure__ne=True,
            flag_completed=False)
