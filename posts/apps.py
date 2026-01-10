from django.apps import AppConfig
import logging
import os

logger = logging.getLogger(__name__)


class PostsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'posts'
    
    def ready(self):
        """Preload summarization models when Django starts."""
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
        
        try:
            from posts.utils.summarizer import preload_summarizer
            # Preload models synchronously to ensure they're ready before server accepts requests
            # This blocks startup but ensures first request is fast (takes ~30-60 seconds)
            logger.info("Preloading summarization models synchronously (this may take 30-60 seconds)...")
            preload_summarizer()
            logger.info("✓ Summarization models preloaded successfully - server ready to accept requests")
        except Exception as e:
            logger.error(f"✗ Failed to preload summarization models: {e}", exc_info=True)
            # Continue anyway - models will load on first request (slower)
            logger.warning("Server will start but first summarization request will be slow")

