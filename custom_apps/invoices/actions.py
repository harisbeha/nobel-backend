from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse


def send_to_provider(modeladmin, request, queryset):
    errors = []
    for job in queryset:
        url = reverse('admin:%s_%s_change' % (job._meta.app_label, job._meta.model_name), args=[job.id])
        email = job.work_order.vendor.system_user.email
        try:
            send_mail('Report ready for review', 'Your work is ready for review: {}'.format(url), 'mail@nobelw.co',
                      [email], fail_silently=False)
            # tick()
        except:
            errors.append(job.id)
    if errors:
        modeladmin.message_user(request, 'Failed to send emails for jobs: %s' % ', '.join(errors), level=messages.ERROR)
