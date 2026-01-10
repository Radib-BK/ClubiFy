"""
Text summarization utility using Hugging Face Inference API.

Recommended models (in order of quality):
1. facebook/bart-large-cnn - Best quality, slower (recommended)
2. sshleifer/distilbart-cnn-12-6 - Good quality, faster
3. google/pegasus-xsum - Good for abstractive summaries
4. Falconsai/text_summarization - Current model (may have length limits)
"""
import os
import logging

os.environ.setdefault('GIT_PYTHON_REFRESH', 'quiet')

logger = logging.getLogger(__name__)

# Default model - can be overridden via environment variable
DEFAULT_MODEL = os.getenv('HF_SUMMARIZATION_MODEL', 'facebook/bart-large-cnn')

# Try to import huggingface_hub for Inference API
try:
    from huggingface_hub import InferenceClient
    HF_INFERENCE_AVAILABLE = True
except ImportError:
    HF_INFERENCE_AVAILABLE = False
    InferenceClient = None

# Hugging Face Inference client (initialized lazily)
_hf_client = None


def get_hf_client():
    """Get or initialize the Hugging Face Inference client."""
    global _hf_client
    if not HF_INFERENCE_AVAILABLE:
        return None
    
    if _hf_client is None:
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            logger.warning("HF_TOKEN not found in environment variables. Hugging Face Inference API will not be available.")
            return None
        
        try:
            _hf_client = InferenceClient(
                provider="hf-inference",
                api_key=hf_token,
            )
            logger.info("Hugging Face Inference client initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Hugging Face Inference client: {e}")
            return None
    
    return _hf_client


def summarize_text(text, max_length=1000, min_length=50):
    """
    Summarize text using Hugging Face Inference API.
    
    Args:
        text: The text to summarize
        max_length: Maximum length of the summary in tokens (default: 1000)
        min_length: Minimum length of the summary in tokens (default: 50)
    
    Returns:
        tuple: (summary_text, is_fallback) where is_fallback is True if truncated fallback was used
    """
    if not text or len(text.strip()) < 50:
        return (text, False)
    
    try:
        client = get_hf_client()
        if client is None:
            logger.warning("Hugging Face Inference client not available")
            # Fallback: return truncated text
            fallback_text = text[:300] + "..." if len(text) > 300 else text
            return (fallback_text, True)
        
        # Truncate text if it's too long (API has limits)
        # BART models typically handle up to ~1024 tokens (~4000 chars), but some models are more restrictive
        # For safety, we'll use a more conservative limit for BART models
        original_text = text
        model_name = DEFAULT_MODEL
        
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
        
        # Call the summarization API
        logger.debug(f"Using summarization model: {model_name}")
        
        # Try to pass max_length and min_length as keyword arguments
        # For BART models, use more conservative limits to avoid "index out of range" errors
        try:
            if 'bart' in model_name.lower():
                # BART models work better with specific token limits
                # Use conservative values to avoid errors
                result = client.summarization(
                    text,
                    model=model_name,
                    max_length=min(max_length, 142),  # BART default max_length is 142 tokens
                    min_length=min(min_length, 56),   # BART default min_length is 56 tokens
                )
            else:
                result = client.summarization(
                    text,
                    model=model_name,
                    max_length=max_length,
                    min_length=min_length,
                )
        except TypeError:
            # If keyword arguments don't work, try without them
            logger.debug("max_length/min_length parameters not supported, using defaults")
            result = client.summarization(
                text,
                model=model_name,
            )
        except Exception as e:
            # If the model fails with a 400 error (like "index out of range"), try a fallback model
            error_str = str(e).lower()
            if '400' in error_str or 'bad request' in error_str or 'index out of range' in error_str:
                logger.warning(f"Model {model_name} failed with input length issue: {e}")
                if model_name != 'sshleifer/distilbart-cnn-12-6':
                    logger.info("Trying fallback model: sshleifer/distilbart-cnn-12-6 with shorter input")
                    try:
                        # Use even shorter input for fallback model
                        fallback_text = text[:1000] if len(text) > 1000 else text
                        result = client.summarization(
                            fallback_text,
                            model='sshleifer/distilbart-cnn-12-6',
                        )
                        model_name = 'sshleifer/distilbart-cnn-12-6'
                        text = fallback_text  # Update text for logging
                        logger.info(f"Fallback model succeeded with {len(fallback_text)} character input")
                    except Exception as e2:
                        logger.error(f"Fallback model also failed: {e2}")
                        raise e
                else:
                    raise e
            else:
                raise e
        
        # Handle different response formats
        # The API returns a SummarizationOutput object with summary_text attribute
        if result:
            summary = None
            
            # Check if it's a SummarizationOutput object (has summary_text attribute)
            if hasattr(result, 'summary_text'):
                summary = result.summary_text
                logger.debug(f"Extracted summary from SummarizationOutput object, length: {len(summary) if summary else 0}")
            # Check if it's a dict-like object
            elif isinstance(result, dict):
                summary = result.get('summary_text', '')
                logger.debug(f"Extracted summary from dict, length: {len(summary) if summary else 0}")
            # Check if it's a string
            elif isinstance(result, str):
                summary = result
                logger.debug(f"Summary is string, length: {len(summary)}")
            # Check if it's a list
            elif isinstance(result, list) and len(result) > 0:
                if hasattr(result[0], 'summary_text'):
                    summary = result[0].summary_text
                elif isinstance(result[0], dict):
                    summary = result[0].get('summary_text', '')
                elif isinstance(result[0], str):
                    summary = result[0]
                logger.debug(f"Extracted summary from list, length: {len(summary) if summary else 0}")
            
            if summary and summary.strip():
                summary = summary.strip()
                logger.info(f"Summary extracted successfully, length: {len(summary)} characters")
                logger.info(f"Full summary content: {summary}")
                # Check if the summary is just the truncated original (fallback)
                truncated_original = original_text[:300] + "..." if len(original_text) > 300 else original_text
                if summary == truncated_original.strip():
                    logger.warning("Summary matches truncated original, treating as fallback")
                    return (summary, True)
                return (summary, False)
            else:
                logger.warning("Summary is empty or None after extraction")
    except Exception as e:
        logger.error(f"Hugging Face Inference API summarization failed: {e}")
    
    # Fallback: return truncated text if summarization fails
    fallback_text = text[:300] + "..." if len(text) > 300 else text
    return (fallback_text, True)
