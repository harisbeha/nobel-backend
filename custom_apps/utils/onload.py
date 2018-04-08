import os


def setup():
    from django.conf import settings
    try:
        import googleclouddebugger
        googleclouddebugger.enable(version='v0.0.1', module='backend', project_id='nobel-weather-associates',
                                   project_number='419191605818',
                                   service_account_json_file=settings.GOOGLE_CLOUD_JSON,
                                   enable_service_account_auth=True)
    except ImportError:
        pass
