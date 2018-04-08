from audit_trail import AuditTrailWatcher
from django.db import models
from django_auto_one_to_one import AutoOneToOneModel


class DummyUserNotifier(models.Model):
    user = AutoOneToOneModel('auth.User')

    audit = AuditTrailWatcher(track_related=['user'])
