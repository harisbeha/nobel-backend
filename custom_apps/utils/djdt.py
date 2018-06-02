from django.conf import settings
import os

def callback(request):
  return os.environ.get('SHOW_DEBUG_TOOLBAR', True) 
