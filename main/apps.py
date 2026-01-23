from django.apps import AppConfig
import logging
from django.urls import get_resolver
logger = logging.getLogger(__name__)

class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        logger.info("Main app is ready")
        # Get all URL patterns
        url_patterns = get_resolver().url_patterns
        logger.info("URL patterns loaded: %s", url_patterns)
