from django.contrib.admin import register, ModelAdmin
from import_export.admin import ImportExportActionModelAdmin
from django.shortcuts import HttpResponseRedirect
from django.conf.urls import url
from django.forms import ModelForm
import sendgrid
import os
from sendgrid.helpers.mail import *
from django.conf import settings
from import_export.admin import ExportMixin

from ..models import *
from ..resources import *
from django.forms.models import BaseModelFormSet

from django.forms.models import BaseInlineFormSet, BaseFormSet
import nested_admin
from raven import Client
from .helpers import get_locations_by_system_user


class SafetyReportForm(ModelForm):
    fields = '__all__'
    model = SafetyReport

    def __init__(self, *args, **kwargs):
        super(SafetyReportForm, self).__init__(*args, **kwargs)
        # init_build = self.initial.get('building')
        # b = Building.objects.get(id=init_build).service_provider
        # self.fields.building.queryset = Building.objects.filter(service_provider=b)


class SRFormSet(BaseInlineFormSet):
    model = SafetyReport
    # form = SafetyReportForm

    def __init__(self, *args, **kwargs):
        super(SRFormSet, self).__init__(*args, **kwargs)
        for form in self.forms:
            try:
                init_build = form.initial.get('building')
                b = Building.objects.get(id=init_build).service_provider
                form.fields['building'].queryset = Building.objects.filter(service_provider=b)
            except:
                pass
        if self.request.user.is_superuser:
            #print('yes')
            self.locations = get_locations_by_system_user(None, self.instance.service_provider)
        else:
            self.locations = get_locations_by_system_user(self.request.user, None)


class WOFormSet(BaseInlineFormSet):
    model = WorkOrder

    def __init__(self, *args, **kwargs):
        super(WOFormSet, self).__init__(*args, **kwargs)
        for form in self.forms:
            try:
                init_build = form.initial.get('building')
                b = Building.objects.get(id=init_build).service_provider
                form.fields['building'].queryset = Building.objects.filter(service_provider=b)
            except:
                pass
        if self.request.user.is_superuser:
            #print('yes')
            self.locations = get_locations_by_system_user(None, self.instance.service_provider)
        else:
            self.locations = get_locations_by_system_user(self.request.user, None)
