"""base URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.views.static import serve
from custom_apps.invoices.admin import nwa_site, cbre_site, vendor_site


SITE_NAME = 'Nobel Weather Associates'
admin.site.site_url = None
admin.site.site_header = SITE_NAME
admin.site.site_title = SITE_NAME
admin.site.index_title = SITE_NAME

urlpatterns = [
    #url(r'^jet/', include('jet.urls', 'jet')),
    url(r'^static/(?P<path>.*)', serve, kwargs={'document_root': settings.STATIC_ROOT}),
    url(r'^admin/', admin.site.urls),
    url(r'^nwa/', nwa_site.urls),
    url(r'^cbre/', cbre_site.urls),
    url(r'^provider/', vendor_site.urls),
    url(r'^admin/', include("massadmin.urls")),
    url(r'^nested_admin/', include('nested_admin.urls')),
    url(r'^hijack/', include('hijack.urls', namespace='hijack')),
    url(r'^adminactions/', include('adminactions.urls')),
    url(r'^', include('favicon.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
