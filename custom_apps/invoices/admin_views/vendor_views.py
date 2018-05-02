from django.contrib.admin import register, ModelAdmin, StackedInline
from import_export.admin import ImportExportActionModelAdmin

from django import forms
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template import loader

from base import settings
from custom_apps.invoices.admin_views.common import AppendOnlyMixin
from custom_apps.invoices.models import SafetyReport, WorkVisit, DiscrepancyReport, WorkOrder
from ..models import WorkOrderProxyVendor, Vendor
from ..enums import Group


# all the views in this file should be visible only to vendor
class VendorModelAdmin(ImportExportActionModelAdmin):
    def has_module_permission(self, request):
        if request.user.groups.filter(name='Vendor').count() > 0:
            return True
        return False


# this is the inline for adding safety reports to a workorder
class SafetyReportInline(StackedInline, AppendOnlyMixin):
    extra = 0
    model = SafetyReport

    model.work_order.flag_safe = model.safe_to_open

    def has_add_permission(self, request):
        return self.model.work_order.get_queryset().filter(flag_safe=False).exists()


# this is the inline for adding work visits to a workorder
class WorkVisitInline(StackedInline, AppendOnlyMixin):
    extra = 0
    model = WorkVisit


    def has_add_permission(self, request):
        return not self.model.work_order.get_queryset().filter(flag_visitsdocumented=True).exists()


class DiscrepancyReportForm(forms.ModelForm):
    class Meta:
        model = DiscrepancyReport
        fields = ['message']
        exclude = ['author', 'work_order']


# this is the inline for adding discrepancy reports to a workorder
class DiscrepancyReportInline(StackedInline, AppendOnlyMixin):
    extra = 0
    model = DiscrepancyReport
    form = DiscrepancyReportForm

    # TODO: set parent's flag_hasdiscrepancies = None and send email on creation

    def get_readonly_fields(self, request, obj=None):
        # TODO: figure out a way to get this list dynamically
        return {'author'}

    def has_add_permission(self, request):
        if self.model.work_order.get_queryset().filter(flag_hasdiscrepancies=True).exists() \
            and self.model.work_order.get_queryset().filter(flag_hasdiscrepanciesfailure=False).exists():
            return True;
        else:
            return False;

def mark_visitsdocumented(modeladmin, request, queryset):
    for workorder in queryset:
        workorder.flag_visitsdocumented = True
        workorder.save()

mark_visitsdocumented.short_description = 'Mark as visits documented'


class VendorWorkOrderForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = ['building']

# this is the admin for creating and editing workorders
@register(WorkOrderProxyVendor)
class VendorCreatesWorkOrders(VendorModelAdmin):
    # TODO: widget for searching for buildings during object creation
    # TODO: add to weather processing queue on creation
    # TODO: action to mark flag_visitsdocumented = True

    actions = [mark_visitsdocumented,]
    inlines = [SafetyReportInline, WorkVisitInline, DiscrepancyReportInline]
    list_filter = ('flag_hasdiscrepancies', 'flag_hasdiscrepanciesfailure')
    list_display = ['vendor', 'invoice', 'building', 'storm_name']
    raw_id_fields = ('building',)
    exclude = ('vendor', 'invoice', 'flag_safe', 'flag_visitsdocumented', 'flag_weatherready', 'flag_failure', 'flag_hasdiscrepancies', 'flag_hasdiscrepanciesfailure', 'flag_completed',)
    form = VendorWorkOrderForm
    fieldsets = ('wtf', {'fields': ('building',)})


    def get_exclude(self, request, obj=None):
        """
        Hook for specifying exclude.
        """
        return ['vendor', 'invoice', 'flag_safe', 'flag_visitsdocumented', 'flag_weatherready', 'flag_failure', 'flag_hasdiscrepancies', 'flag_hasdiscrepanciesfailure', 'flag_completed']


    def get_changeform_initial_data(self, request):
        initial = super(VendorCreatesWorkOrders, self).get_changeform_initial_data(request)
        vendors = Vendor.objects.filter(system_user__groups__name=Group.VENDOR.value).order_by('name')
        uservendor = Vendor.objects.filter(system_user=request.user)
        print(vendors.values_list('name'))
        print(uservendor.values_list('name'))
        initial['vendor'] = list(vendors.values_list('name')).index(uservendor.values_list('name')[0]) + 1
        print(initial)
        return initial

    def get_queryset(self, request):
        qs = super(VendorCreatesWorkOrders, self).get_queryset(request).filter(vendor__system_user=request.user)
        return qs

    def get_readonly_fields(self, request, obj=None):
        # TODO: figure out a way to get this list dynamically
        return {'vendor'}

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.flag_completed:
            return False
        return True  # TODO: is this the right thing to do?

    def save_model(self, request, obj, form, change):
        instance = form.save(commit=False)
        if not change:  # new object
            instance.vendor = Vendor.objects.filter(system_user__exact=request.user).first()
            text_template = loader.get_template('mail_template_new_work_order.txt')
            context = {
                'work_order': instance,
            }
            mail = EmailMultiAlternatives(
                subject="You have created a new work order " + instance,
                body=text_template.render(context),
                to=[request.user.email],
            )
        # else:             # updated old object
        #   modify object

        instance.save()
        form.save_m2m()
        return instance

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        for instance in instances:
            if type(instance) == DiscrepancyReport:
                instance.author = request.user
                instance.work_order.flag_hasdiscrepancies = None
                nwa_users = User.objects.filter(groups__name=Group.NWA.value).values_list('user__email')
                text_template = loader.get_template('mail_template_new_discrepancy_report.txt')
                context = {
                    'user': request.user,
                    'work_order': instance,
                }
                mail = EmailMultiAlternatives(
                    subject="New discrepancy report for work order " + instance,
                    body=text_template.render(context),
                    to=[nwa_users],
                )

            instance.save()

        formset.save_m2m()

    def get_formsets_with_inlines(self, request, obj=None): # bam
        for formset in super(VendorCreatesWorkOrders, self).get_formsets_with_inlines(request, obj=obj):

            yield formset