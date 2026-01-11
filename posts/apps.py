from django.apps import AppConfig
import logging
import os
import threading

logger = logging.getLogger(__name__)


class PostsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'posts'
    
    def ready(self):
        """Preload summarization models when Django starts (asynchronously to avoid blocking)."""
        logger.info("PostsConfig.ready() called - initializing summarizer preload")
        
        # Skip preloading during migrations and other management commands
        import sys
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv or 'collectstatic' in sys.argv:
            logger.info("Skipping summarizer preload (management command detected)")
            return
        
        # Check if preloading is disabled via environment variable
        skip_preload = os.getenv('SKIP_SUMMARIZER_PRELOAD', 'false').lower() == 'true'
        if skip_preload:
            logger.info("Skipping summarizer preload (SKIP_SUMMARIZER_PRELOAD=true)")
            return
        
        # Preload models asynchronously in background thread to avoid blocking Django startup
        # This allows the server to start immediately while models load in the background
        def preload_in_background():
            try:
                from posts.utils.summarizer import preload_summarizer
                logger.info("Preloading summarization models in background (this may take 30-60 seconds)...")
                logger.info("Django server is starting - models will be ready shortly")
                preload_summarizer()
                logger.info("✓ Summarization models preloaded successfully - ready for requests")
            except Exception as e:
                logger.error(f"✗ Failed to preload summarization models: {e}", exc_info=True)
                logger.warning("Models will load on first request (slower)")
        
        # Start preloading in background thread (daemon thread so it doesn't prevent shutdown)
        thread = threading.Thread(target=preload_in_background, daemon=True)
        thread.start()
        logger.info("Summarizer preload started in background - Django server starting immediately")

