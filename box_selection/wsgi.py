"""
WSGI config for box_selection project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'box_selection.settings')
application = get_wsgi_application()
