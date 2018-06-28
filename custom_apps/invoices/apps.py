# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig
import hijack

class InvoicesConfig(AppConfig):
    name = 'custom_apps.invoices'
    verbose_name = 'Manage'

    def ready(self):
        r = super(InvoicesConfig, self).ready()

        from . import signals   # late import bc models aren't ready yet
        signals.connect_state_workflow()
        import hijack.helpers

        hijack.helpers.login_user = o_login_user

        return r


def o_login_user(request, hijacked):
    ''' hijack mechanism '''
    hijacker = request.user
    hijack_history = [request.user._meta.pk.value_to_string(hijacker)]
    if request.session.get('hijack_history'):
        hijack_history = request.session['hijack_history'] + hijack_history

    hijack.helpers.check_hijack_authorization(request, hijacked)

    backend = hijack.helpers.get_used_backend(request)
    hijacked.backend = "%s.%s" % (backend.__module__, backend.__class__.__name__)

    with hijack.helpers.no_update_last_login():
        # Actually log user in
        hijack.helpers.login(request, hijacked)

    hijack.signals.hijack_started.send(
        sender=None, request=request,
        hijacker=hijacker, hijacked=hijacked,
        # send IDs for backward compatibility
        hijacker_id=hijacker.pk, hijacked_id=hijacked.pk)
    request.session['hijack_history'] = hijack_history
    request.session['is_hijacked_user'] = True
    request.session['display_hijack_warning'] = True
    request.session.modified = True


    role = get_main_user_role(hijacker)
    if role == 'admin':
        default_url = '/admin/'
    elif role == 'nwa':
        default_url = '/nwa/'
    elif role == 'cbre':
        default_url = '/cbre/'
    elif role == 'provider':
        default_url = '/provider/'
    else:
        default_url = '/provider/'

    return hijack.helpers.redirect_to_next(request, default_url=default_url)

def get_main_user_role(user):
    return 'provider'