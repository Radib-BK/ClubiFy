"""
Text summarization utility using spaCy and PyTextRank.
"""
import os
import re
import spacy
import pytextrank

# Suppress git warnings from pytextrank
os.environ.setdefault('GIT_PYTHON_REFRESH', 'quiet')

# Initialize NLP model (loaded once, reused across requests)
_nlp = None

def get_nlp():
    """Get or initialize the spaCy NLP model with TextRank pipeline."""
    global _nlp
    if _nlp is None:
        # Use medium model for better word vectors (improves PyTextRank quality)
        try:
            _nlp = spacy.load("en_core_web_md")
        except OSError:
            # Fallback to small model if medium not available
            _nlp = spacy.load("en_core_web_sm")
        _nlp.add_pipe("textrank")
    return _nlp


def clean_sentence(text):
    """Clean sentence by removing leading conjunctions and extra whitespace."""
    text = text.strip()
    # Remove leading conjunctions that make summaries sound unprofessional
    text = re.sub(r"^(But|And|So|Because|However|Although|Though)\s+", "", text, flags=re.IGNORECASE)
    return text


def summarize_text(text, limit_sentences=None):
    """
    Summarize text using PyTextRank with improved sentence selection.
    
    Args:
        text: The text to summarize
        limit_sentences: Number of sentences in summary (auto-calculated if None)
    
    Returns:
        str: Summarized text
    """
    if not text or len(text.strip()) < 50:
        return text
    
    nlp = get_nlp()
    doc = nlp(text)
    
    # Get all sentences
    sentences = list(doc.sents)
    sentence_count = len(sentences)
    
    # Auto-calculate limit based on sentence count (better than word count)
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
    
    # Get ranked sentences (get more than needed for diversity)
    ranked = list(doc._.textrank.summary(limit_sentences=limit * 2))
    
    # Select sentences with paragraph diversity
    selected = []
    used_paragraphs = set()
    
    for sent in ranked:
        # Group sentences into rough paragraph buckets (every ~200 chars)
        para_id = sent.start // 200
        
        # Only add if from a different paragraph (ensures diversity)
        if para_id not in used_paragraphs or len(selected) < 2:
            cleaned = clean_sentence(sent.text)
            if cleaned:  # Only add non-empty cleaned sentences
                selected.append(cleaned)
                used_paragraphs.add(para_id)
        
        # Stop when we have enough sentences
        if len(selected) >= limit:
            break
    
    # Fallback: if diversity filtering removed too many, use top-ranked
    if len(selected) < limit:
        selected = [clean_sentence(sent.text) for sent in ranked[:limit]]
        selected = [s for s in selected if s]  # Remove empty strings
    
    # Join sentences with proper spacing and strip any leading/trailing whitespace
    summary = ' '.join(selected).strip()
    
    return summary if summary else text[:300] + "..." if len(text) > 300 else text

