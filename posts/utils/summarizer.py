"""
Text summarization utility using Hugging Face transformers.

Using sshleifer/distilbart-cnn-12-6 - Good quality, faster, lower memory usage.
"""
import os
import logging
import threading

os.environ.setdefault('GIT_PYTHON_REFRESH', 'quiet')

logger = logging.getLogger(__name__)

# Default model - can be overridden via environment variable
DEFAULT_MODEL = os.getenv('HF_SUMMARIZATION_MODEL', 'sshleifer/distilbart-cnn-12-6')
FALLBACK_MODEL = 'sshleifer/distilbart-cnn-12-6'  # Same as default (fallback logic kept for compatibility)

# Hugging Face summarizers (cached per model)
_hf_summarizers = {}
_hf_lock = threading.Lock()

def get_hf_summarizer(model_name=None):
    """Get or initialize the Hugging Face summarization pipeline for a specific model."""
    global _hf_summarizers
    if model_name is None:
        model_name = DEFAULT_MODEL
    
    if model_name not in _hf_summarizers:
        with _hf_lock:
            # Double-check pattern to avoid race conditions
            if model_name not in _hf_summarizers:
                try:
                    from transformers import pipeline
                    logger.info(f"Loading Hugging Face summarization model: {model_name} (this may take 30-60 seconds on first load)...")
                    logger.info("This is normal on first use - the model needs to be downloaded and loaded into memory.")
                    _hf_summarizers[model_name] = pipeline("summarization", model=model_name)
                    logger.info(f"Hugging Face summarization model {model_name} loaded successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize Hugging Face summarizer with {model_name}: {e}", exc_info=True)
                    _hf_summarizers[model_name] = False  # Set to False to indicate it's unavailable
    return _hf_summarizers.get(model_name)


def preload_summarizer():
    """Preload the summarizer model at startup to avoid first-request delay."""
    try:
        logger.info("Preloading summarization model...")
        logger.info(f"Loading model: {DEFAULT_MODEL} (this may take 20-40 seconds)...")
        # Preload the Hugging Face model
        summarizer = get_hf_summarizer(DEFAULT_MODEL)
        if summarizer is False or summarizer is None:
            logger.warning(f"Failed to load model {DEFAULT_MODEL}")
        else:
            logger.info(f"✓ Model {DEFAULT_MODEL} loaded successfully")
            logger.info("✓ Summarization model preloaded - ready for requests")
    except Exception as e:
        logger.error(f"Failed to preload summarization model: {e}", exc_info=True)
        # Don't raise - allow the app to start even if model fails to load


def summarize_with_hf(text, max_length=300, min_length=50, model_name=None):
    """
    Summarize text using Hugging Face transformers.
    
    Args:
        text: The text to summarize
        max_length: Maximum length of the summary in tokens (default: 300)
        min_length: Minimum length of the summary in tokens (default: 50)
        model_name: Model to use (default: DEFAULT_MODEL)
    
    Returns:
        str: Summarized text, or None if summarization fails
    """
    if model_name is None:
        model_name = DEFAULT_MODEL
    
    original_text = text
    
    # Check if model previously failed and retry if needed
    if model_name in _hf_summarizers and _hf_summarizers[model_name] is False:
        logger.warning(f"Model {model_name} previously failed to load, trying again...")
        # Clear the failed state and try again
        with _hf_lock:
            if model_name in _hf_summarizers and _hf_summarizers[model_name] is False:
                del _hf_summarizers[model_name]
    
    try:
        # Different models have different input length limits
        if 'bart' in model_name.lower():
            # BART models are more restrictive - limit to ~1500 characters (~384 tokens)
            # This is more conservative to avoid "index out of range" errors
            max_input_length = 1500
        else:
            # Other models can handle more
            max_input_length = 4000
        
        if len(text) > max_input_length:
            logger.debug(f"Truncating input text from {len(text)} to {max_input_length} characters for model {model_name}")
            text = text[:max_input_length]
        
        # Try to get or create summarizer with the specified model
        # Note: This will use the cached summarizer if it exists, so we may need to handle model switching
        summarizer = get_hf_summarizer(model_name)
        if summarizer is False or summarizer is None:
            logger.warning(f"Summarizer for {model_name} is not available (may still be loading)")
            return None
        
        # For BART models, use more conservative limits to avoid errors
        if 'bart' in model_name.lower():
            # BART default max_length is 142 tokens, min_length is 56 tokens
            effective_max_length = min(max_length, 142)
            effective_min_length = min(min_length, 56)
        else:
            effective_max_length = max_length
            effective_min_length = min_length
        
        # Use max_new_tokens instead of max_length to avoid parameter conflicts
        result = summarizer(
            text, 
            max_new_tokens=effective_max_length, 
            min_length=effective_min_length, 
            do_sample=False
        )
        
        if result and isinstance(result, list) and len(result) > 0:
            summary = result[0].get('summary_text', '')
            if summary:
                summary = summary.strip()
                logger.debug(f"Summary extracted successfully from {model_name}, length: {len(summary)} characters")
                return summary
    except Exception as e:
        error_str = str(e).lower()
        # If the model fails with input length issues, try fallback model
        if ('400' in error_str or 'bad request' in error_str or 'index out of range' in error_str or 
            'length' in error_str) and model_name != FALLBACK_MODEL:
            logger.warning(f"Model {model_name} failed with input length issue: {e}")
            logger.info(f"Trying fallback model: {FALLBACK_MODEL} with shorter input")
            try:
                # Use even shorter input for fallback model
                fallback_text = original_text[:1000] if len(original_text) > 1000 else original_text
                return summarize_with_hf(fallback_text, max_length, min_length, FALLBACK_MODEL)
            except Exception as e2:
                logger.error(f"Fallback model {FALLBACK_MODEL} also failed: {e2}")
        else:
            logger.warning(f"Hugging Face summarization failed with {model_name}: {e}")
    
    return None


def summarize_text(text, max_length=300, min_length=50):
    """
    Summarize text using Hugging Face transformers with automatic fallback to secondary model.
    
    Args:
        text: The text to summarize
        max_length: Maximum length of the summary in tokens (default: 300)
        min_length: Minimum length of the summary in tokens (default: 50)
    
    Returns:
        str: Summarized text, or truncated text if summarization fails
    """
    if not text or len(text.strip()) < 50:
        return text
    
    # Try Hugging Face summarizer (with automatic fallback to secondary model)
    summary = summarize_with_hf(text, max_length, min_length)
    
    if summary:
        return summary
    
    # Final fallback: return truncated text
    logger.warning("All summarization methods failed, returning truncated text")
    return text[:300] + "..." if len(text) > 300 else text

