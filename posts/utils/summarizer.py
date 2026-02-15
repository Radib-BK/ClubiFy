"""
Text summarization utility using Hugging Face transformers.

Using sshleifer/distilbart-cnn-12-6 - Good quality, faster, lower memory usage.
Model is pre-downloaded during Docker build, so no runtime downloads needed.
"""

import os
import logging
import threading

os.environ.setdefault("GIT_PYTHON_REFRESH", "quiet")

# Set Hugging Face cache directory if not already set
os.environ.setdefault("HF_HOME", "/app/.cache/huggingface")

logger = logging.getLogger(__name__)

# Default model
DEFAULT_MODEL = os.getenv("HF_SUMMARIZATION_MODEL", "sshleifer/distilbart-cnn-12-6")

# Hugging Face summarizers (cached per model)
_hf_summarizers = {}
_hf_lock = threading.Lock()


def get_hf_summarizer(model_name=None):
    """Get or initialize the Hugging Face summarization pipeline."""
    global _hf_summarizers
    if model_name is None:
        model_name = DEFAULT_MODEL

    if model_name not in _hf_summarizers:
        with _hf_lock:
            # Double-check pattern to avoid race conditions
            if model_name not in _hf_summarizers:
                try:
                    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

                    logger.info(f"Loading Hugging Face model: {model_name}")

                    # Model should already be cached from Docker build
                    tokenizer = AutoTokenizer.from_pretrained(model_name)
                    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

                    _hf_summarizers[model_name] = {
                        "tokenizer": tokenizer,
                        "model": model,
                    }
                    logger.info(f"Model {model_name} loaded successfully")
                except Exception as e:
                    logger.error(
                        f"Failed to load model {model_name}: {e}", exc_info=True
                    )
                    _hf_summarizers[model_name] = False

    return _hf_summarizers.get(model_name)


def preload_summarizer():
    """Preload the summarizer model at startup."""
    try:
        logger.info("Preloading summarization model...")
        summarizer = get_hf_summarizer(DEFAULT_MODEL)
        if summarizer is False or summarizer is None:
            logger.warning(f"Failed to load model {DEFAULT_MODEL}")
        else:
            logger.info(f"✓ Model {DEFAULT_MODEL} loaded successfully")
    except Exception as e:
        logger.error(f"Failed to preload summarization model: {e}", exc_info=True)


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

    try:
        # BART models have restrictive limits
        if "bart" in model_name.lower():
            max_input_length = 1500
            effective_max_length = min(max_length, 142)
            effective_min_length = min(min_length, 56)
        else:
            max_input_length = 4000
            effective_max_length = max_length
            effective_min_length = min_length

        # Truncate long inputs
        if len(text) > max_input_length:
            logger.debug(
                f"Truncating input from {len(text)} to {max_input_length} characters"
            )
            text = text[:max_input_length]

        # Load model
        summarizer = get_hf_summarizer(model_name)
        if summarizer is False or summarizer is None:
            logger.warning(f"Summarizer for {model_name} is not available")
            return None

        tokenizer = summarizer["tokenizer"]
        model = summarizer["model"]

        # Tokenize input
        inputs = tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)

        # Generate summary
        summary_ids = model.generate(
            inputs["input_ids"],
            max_length=effective_max_length,
            min_length=effective_min_length,
            num_beams=4,
            length_penalty=2.0,
            early_stopping=True,
        )

        # Decode summary
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

        if summary:
            summary = summary.strip()
            logger.debug(f"Summary generated, length: {len(summary)} characters")
            return summary

    except Exception as e:
        logger.error(f"Hugging Face summarization failed: {e}", exc_info=True)
        logger.debug(f"Error details: {type(e).__name__}: {e}")

    return None


def summarize_text(text, max_length=300, min_length=50):
    """
    Summarize text using Hugging Face transformers.

    Args:
        text: The text to summarize
        max_length: Maximum length of the summary in tokens (default: 300)
        min_length: Minimum length of the summary in tokens (default: 50)

    Returns:
        str: Summarized text, or truncated text if summarization fails
    """
    if not text or len(text.strip()) < 50:
        return text

    # Try Hugging Face summarizer
    summary = summarize_with_hf(text, max_length, min_length)

    if summary:
        return summary

    # Fallback: return truncated text
    logger.warning("Summarization failed, returning truncated text")
    return text[:300] + "..." if len(text) > 300 else text
