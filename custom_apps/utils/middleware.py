from django.http import HttpResponse


class PermissionsErrorMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            if request.path.startswith('/admin/') and request.user.groups.count() > 1 and not request.user.is_superuser:
                return HttpResponse('Your user is configured incorrectly. '
                                    'Please contact <a href="mailto:support@nobelw.co">support@nobelw.co</a> '
                                    'for further assistance.',
                                    status=400)
        except:
            pass
        return self.get_response(request)
