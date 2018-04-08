"""
WSGI config for base project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from custom_apps.utils import debugger

debugger.setup()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "base.settings")

application = get_wsgi_application()
