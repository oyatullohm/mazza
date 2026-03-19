import firebase_admin
from firebase_admin import credentials
from django.conf import settings

if not firebase_admin._apps:
    cred = credentials.Certificate(settings.HOME_URL)
    firebase_admin.initialize_app(cred)