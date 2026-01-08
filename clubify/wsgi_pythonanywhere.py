"""
WSGI config for clubify project - PythonAnywhere specific version.

This file should be used as your WSGI file in PythonAnywhere's Web tab.
Point the WSGI configuration file to: /home/yourusername/ClubiFy/clubify/wsgi_pythonanywhere.py
"""

import os
import sys

# Add your project directory to the Python path
path = '/home/yourusername/ClubiFy'  # CHANGE THIS to your actual path
if path not in sys.path:
    sys.path.insert(0, path)

# Set the Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'clubify.settings'

# Set PythonAnywhere username (replace 'yourusername' with your actual username)
os.environ['PA_USERNAME'] = 'yourusername'  # CHANGE THIS

# Import Django's WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
