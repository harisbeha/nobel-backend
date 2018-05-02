# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class InvoicesConfig(AppConfig):
    name = 'custom_apps.invoices'
    verbose_name = 'Manage'

    def ready(self):
        r = super(InvoicesConfig, self).ready()

        from . import signals   # late import bc models aren't ready yet
        signals.connect_state_workflow()

        return r

