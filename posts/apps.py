from django.apps import AppConfig
import logging
import os

logger = logging.getLogger(__name__)


class PostsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'posts'
    
    def ready(self):
        """Preload summarization models when Django starts."""
        # Skip preloading during migrations and other management commands
        import sys
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv or 'collectstatic' in sys.argv:
            return
        
        # Check if preloading is disabled via environment variable
        skip_preload = os.getenv('SKIP_SUMMARIZER_PRELOAD', 'false').lower() == 'true'
        if skip_preload:
            logger.info("Skipping summarizer preload (SKIP_SUMMARIZER_PRELOAD=true)")
            return
        
        try:
            from posts.utils.summarizer import preload_summarizer
            # Preload in background thread to avoid blocking server startup
            # The model will be ready when first request comes in
            import threading
            thread = threading.Thread(target=preload_summarizer, daemon=True)
            thread.start()
            logger.info("Started background thread to preload summarization models")
        except Exception as e:
            logger.warning(f"Could not start summarizer preload thread: {e}")

