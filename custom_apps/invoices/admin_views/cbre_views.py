from django.contrib.admin import register, ModelAdmin, StackedInline

from ..models import VendorProxyCBRE, WorkOrderProxyCBRE, WorkVisit, SafetyReport
from ..enums import Group
from .common import ReadOnlyMixin


# all the views in this file should be visible only to cbre
class CBREModelAdmin(ModelAdmin):
    def has_module_permission(self, request):
        if request.user.groups.filter(name=Group.CBRE.value).count() > 0:
            return True
        return False


# this is the admin to create vendors
@register(VendorProxyCBRE)
class CBRECreatesVendors(CBREModelAdmin):
    # TODO: any vendor created automatically has the cbre attached

    def has_delete_permission(self, request, obj=None):
        return False


# this is the inline to view workvisits within a workorder
class WorkVisitInline(StackedInline, ReadOnlyMixin):
    model = SafetyReport


# this is the inline to view safety reports within aworkorder
class SafetyReportInline(StackedInline, ReadOnlyMixin):
    model = SafetyReport


@register(WorkOrderProxyCBRE)
class CBREModeratesWorkOrders(CBREModelAdmin):
    # TODO: actions to mark flag_failure = True, False
    # TODO: the save button shouldn't exist. ideally the edit button should say view instead of edit
    # TODO: ideally the edit button should say view instead of edit
    # TODO: evaluate setting has_change_permission to false? that would let us use readonlymixin
    # TODO: port the stuff to inline the vendorsettings creation

    inlines = [WorkVisitInline, SafetyReportInline]

    def get_queryset(self, request):
        qs = super(CBREModeratesWorkOrders, self).get_queryset(request)
        # TODO: filter by vendors under the current user's cbre
        return qs.filter(flag_failure=None)

    def get_readonly_fields(self, request, obj=None):
        return self.model._meta.fields

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True
