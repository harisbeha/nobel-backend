from audit_trail.models import AuditTrailManager

from django_extensions.db.models import TimeStampedModel


class BaseModel(TimeStampedModel):
    class Meta:
        abstract = True

