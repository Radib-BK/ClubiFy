"""
Text summarization utility using Hugging Face transformers with fallback to spaCy and PyTextRank.
"""
import os
import re
import logging
import threading

os.environ.setdefault('GIT_PYTHON_REFRESH', 'quiet')

logger = logging.getLogger(__name__)

# Hugging Face summarizer
_hf_summarizer = None
_hf_lock = threading.Lock()

# spaCy NLP model
_nlp = None
_nlp_lock = threading.Lock()

def get_hf_summarizer():
    """Get or initialize the Hugging Face summarization pipeline."""
    global _hf_summarizer
    if _hf_summarizer is None:
        with _hf_lock:
            # Double-check pattern to avoid race conditions
            if _hf_summarizer is None:
                try:
                    from transformers import pipeline
                    logger.info("Loading Hugging Face summarization model (this may take 10-30 seconds on first load)...")
                    _hf_summarizer = pipeline("summarization", model="Falconsai/text_summarization")
                    logger.info("Hugging Face summarization model loaded successfully")
                except Exception as e:
                    logger.warning(f"Failed to initialize Hugging Face summarizer: {e}")
                    _hf_summarizer = False  # Set to False to indicate it's unavailable
    return _hf_summarizer


def preload_summarizer():
    """Preload the summarizer models at startup to avoid first-request delay."""
    try:
        logger.info("Preloading summarization models...")
        # Preload Hugging Face model
        get_hf_summarizer()
        # Preload spaCy model (optional, but good for consistency)
        get_nlp()
        logger.info("Summarization models preloaded successfully")
    except Exception as e:
        logger.warning(f"Failed to preload summarization models: {e}")
        # Don't raise - allow the app to start even if models fail to load


def get_nlp():
    """Get or initialize the spaCy NLP model with TextRank pipeline."""
    global _nlp
    if _nlp is None:
        with _nlp_lock:
            # Double-check pattern to avoid race conditions
            if _nlp is None:
                try:
                    import spacy
                    import pytextrank
                    _nlp = spacy.load("en_core_web_md")
                except OSError:
                    try:
                        _nlp = spacy.load("en_core_web_sm")
                    except OSError:
                        _nlp = False  # Set to False to indicate it's unavailable
                        return _nlp
                try:
                    _nlp.add_pipe("textrank")
                except Exception as e:
                    logger.warning(f"Failed to add textrank pipe: {e}")
                    _nlp = False
    return _nlp


def clean_sentence(text):
    """Clean sentence by removing leading conjunctions, markdown headers, and extra whitespace."""
    text = text.strip()
    text = re.sub(r"^(But|And|So|Because|However|Although|Though)\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r'^#{1,6}\s+', '', text)
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = text.strip()
    return text


def summarize_with_hf(text, max_length=300, min_length=50):
    """
    Summarize text using Hugging Face transformers.
    
    Args:
        text: The text to summarize
        max_length: Maximum length of the summary in tokens (default: 300)
        min_length: Minimum length of the summary in tokens (default: 50)
    
    Returns:
        str: Summarized text, or None if summarization fails
    """
    try:
        summarizer = get_hf_summarizer()
        if summarizer is False or summarizer is None:
            return None
        
        # Truncate text if it's too long (model has 512 token limit)
        # Roughly 1 token ≈ 4 characters, so ~2000 chars ≈ 500 tokens (safe margin)
        if len(text) > 2000:
            text = text[:2000]
        
        # Use max_new_tokens instead of max_length to avoid parameter conflicts
        # Calculate appropriate max_new_tokens (roughly 40% of input length, capped at max_length)
        result = summarizer(
            text, 
            max_new_tokens=max_length, 
            min_length=min_length, 
            do_sample=False
        )
        
        if result and isinstance(result, list) and len(result) > 0:
            summary = result[0].get('summary_text', '')
            if summary:
                return summary.strip()
    except Exception as e:
        logger.warning(f"Hugging Face summarization failed: {e}")
    
    return None


def summarize_with_spacy(text, limit_sentences=None):
    """
    Summarize text using PyTextRank with improved sentence selection (fallback method).
    
    Args:
        text: The text to summarize
        limit_sentences: Number of sentences in summary (auto-calculated if None)
    
    Returns:
        str: Summarized text
    """
    if not text or len(text.strip()) < 50:
        return text
    
    nlp = get_nlp()
    if nlp is False:
        return None
    
    try:
        doc = nlp(text)
        sentences = list(doc.sents)
        sentence_count = len(sentences)
        
        if limit_sentences is None:
            if sentence_count <= 5:
                limit = 2
            elif sentence_count <= 10:
                limit = 3
            elif sentence_count <= 20:
                limit = 4
            else:
                limit = 5
        else:
            limit = limit_sentences
        
        ranked = list(doc._.textrank.summary(limit_sentences=limit * 2))
        selected = []
        used_paragraphs = set()
        
        for sent in ranked:
            para_id = sent.start // 200
            
            if para_id not in used_paragraphs or len(selected) < 2:
                cleaned = clean_sentence(sent.text)
                if cleaned:
                    selected.append(cleaned)
                    used_paragraphs.add(para_id)
            
            if len(selected) >= limit:
                break
        
        if len(selected) < limit:
            selected = [clean_sentence(sent.text) for sent in ranked[:limit]]
            selected = [s for s in selected if s]
        
        summary = ' '.join(selected).strip()
        
        summary = re.sub(r'\s+', ' ', summary)
        summary = re.sub(r'\s*##+\s*', ' ', summary)
        summary = summary.strip()
        
        return summary if summary else text[:300] + "..." if len(text) > 300 else text
    except Exception as e:
        logger.warning(f"spaCy summarization failed: {e}")
        return None


def summarize_text(text, limit_sentences=None):
    """
    Summarize text using Hugging Face transformers first, with fallback to PyTextRank.
    
    Args:
        text: The text to summarize
        limit_sentences: Number of sentences in summary (for fallback method only)
    
    Returns:
        str: Summarized text
    """
    if not text or len(text.strip()) < 50:
        return text
    
    # Try Hugging Face summarizer first
    summary = summarize_with_hf(text)
    
    if summary:
        return summary
    
    # Fallback to spaCy/PyTextRank
    logger.info("Falling back to spaCy/PyTextRank summarization")
    summary = summarize_with_spacy(text, limit_sentences)
    
    if summary:
        return summary
    
    # Final fallback: return truncated text
    return text[:300] + "..." if len(text) > 300 else text

