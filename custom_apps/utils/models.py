from audit_trail.models import AuditTrailManager


def generate_for_instance(self, instance, action):
    from django.contrib.contenttypes.models import ContentType
    from django.utils.encoding import force_text
    audit_trail = self.model(
        content_type=ContentType.objects.get_for_model(instance),
        object_id=instance.pk,
        object_repr=force_text(instance)[:200],
        action=action
    )

    from audit_trail.utils import get_request
    request = get_request(['user', 'META'])
    if request and hasattr(request, 'user'):
        if request.user.is_authenticated():
            audit_trail.user = request.user
        audit_trail.user_ip = \
            (request.META.get('HTTP_X_FORWARDED_FOR', None) or request.META.get('REMOTE_ADDR')).split(',')[0]
    audit_trail.save()
    return audit_trail


AuditTrailManager.generate_for_instance = generate_for_instance

from django_extensions.db.models import TimeStampedModel


class BaseModel(TimeStampedModel):
    class Meta:
        abstract = True
