from django.contrib.admin import register, ModelAdmin, StackedInline
from django.core.mail import EmailMultiAlternatives

from django.db.models import Q
from django.template import loader

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
    extra = 0
    model = WorkVisit


# this is the inline to view safety reports within a workorder
class SafetyReportInline(StackedInline, ReadOnlyMixin):
    extra = 0
    model = SafetyReport


# this is the inline for viewing and creating discrepancy reports in a workorder
class DiscrepancyReportInline(StackedInline, AppendOnlyMixin):
    extra = 0
    model = DiscrepancyReport


def mark_has_no_discrepancies(modeladmin, request, queryset):
    for workorder in queryset:
        workorder.flag_hasdiscrepancies = False
        workorder.save()

mark_has_no_discrepancies.short_description = 'Mark as having no discrepancies'

def mark_has_discrepancies_failure(modeladmin, request, queryset):
    for workorder in queryset:
        workorder.flag_hasdiscrepanciesfailure = True
        workorder.save()

        text_template = loader.get_template('mail_template_work_order_has_discrepancies.txt')
        context = {
            'user': request.user,
            'work_order': workorder,
        }
        mail = EmailMultiAlternatives(
            subject="There are discrepancies in work order " + workorder,
            body=text_template.render(context),
            to=[workorder.vendor.system_user.email],
        )

mark_has_discrepancies_failure.short_description = 'Mark as failure with discrepancies'


# this is the inline for nwa to moderate work orders
@register(WorkOrderProxyNWA)
class NWAModeratesWorkOrders(NWAModelAdmin):
    # TODO: set flag_hasdiscrepancies = True and send email on discrepancy report - signal?
    # TODO: set authorship for discrepancy orders automatically
    # TODO: evaluate has_change_permission vs get_readonly_fields for inlines

    actions = [mark_has_no_discrepancies, mark_has_discrepancies_failure]
    inlines = [WorkVisitInline, SafetyReportInline, DiscrepancyReportInline]

    def get_readonly_fields(self, request, obj=None):
        # TODO: figure out a way to get this list dynamically
        return {'vendor', 'invoice', 'building', 'storm_name', 'storm_date', 'last_service_date',
                'flag_safe', 'flag_visitsdocumented', 'flag_weatherready', 'flag_failure', 'flag_hasdiscrepancies',
                'flag_hasdiscrepanciesfailure', 'flag_completed'}

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
            flag_completed=False).filter(Q(flag_failure__isnull=True) | Q(flag_failure=False))
