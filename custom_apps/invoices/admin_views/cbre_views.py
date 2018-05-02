
from django.contrib.admin import register, ModelAdmin, StackedInline

from ..models import VendorProxyCBRE, WorkOrderProxyCBRE, WorkVisit, SafetyReport, RegionalAdmin, WorkOrder
from ..enums import Group
from .common import ReadOnlyMixin
from django import forms



# all the views in this file should be visible only to cbre
class CBREModelAdmin(ModelAdmin):
    exclude = ['address_info_storage']
    def has_module_permission(self, request):
        if request.user.groups.filter(name=Group.CBRE.value).count() > 0:
            return True
        return False



# this is the admin to create vendors
@register(VendorProxyCBRE)
class CBRECreatesVendors(CBREModelAdmin):
    list_display = ['name', 'address', 'system_user']

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

def mark_failure(modeladmin, request, queryset):
    for workorder in queryset:
        workorder.flag_failure = True
        workorder.save()

mark_failure.short_description = 'Mark as failure'

def mark_passed(modeladmin, request, queryset):
    for workorder in queryset:
        workorder.flag_failure = False
        workorder.save()

mark_passed.short_description = 'Mark as passed'


class CBREWorkOrderForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = ['vendor', 'invoice']


@register(WorkOrderProxyCBRE)
class CBREModeratesWorkOrders(CBREModelAdmin):
    # TODO: evaluate setting has_change_permission to false? that would let us use readonlymixin
    # TODO: port the stuff to inline the vendorsettings creation

    actions = [mark_passed, mark_failure]
    inlines = [WorkVisitInline, SafetyReportInline]
    list_display = ['vendor', 'invoice', 'building', 'storm_name']
    raw_id_fields = ('building',)
    form = CBREWorkOrderForm

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

