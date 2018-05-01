from django.contrib.admin import register, ModelAdmin, StackedInline

from ..models import VendorProxyCBRE, WorkOrderProxyCBRE, WorkVisit, SafetyReport, RegionalAdmin
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
    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        # TODO: figure out a way to get this list dynamically
        return {'region'}

    def save_model(self, request, obj, form, change):
        user = request.user
        instance = form.save(commit=False)
        if not change:    # new object
            instance.region = RegionalAdmin.objects.filter(system_user__exact=request.user).first()
        #else:             # updated old object
            #   modify object

        instance.save()
        form.save_m2m()
        return instance


# this is the inline to view workvisits within a workorder
class WorkVisitInline(StackedInline, ReadOnlyMixin):
    extra = 0
    model = SafetyReport


# this is the inline to view safety reports within aworkorder
class SafetyReportInline(StackedInline, ReadOnlyMixin):
    extra = 0
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
        qs = super(CBREModeratesWorkOrders, self).get_queryset(request).filter(vendor__region__system_user=request.user)
        return qs.filter(flag_failure=None)

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

    def save_model(self, request, obj, form, change):
        user = request.user
        instance = form.save(commit=False)
        # if not change:    # new object
        #     instance.region = RegionalAdmin.objects.filter(system_user__exact=request.user).first()
        #else:             # updated old object
            #   modify object

        instance.save()
        form.save_m2m()
        return instance