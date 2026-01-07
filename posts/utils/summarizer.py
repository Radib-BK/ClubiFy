"""
Text summarization utility using spaCy and PyTextRank.
"""
import os
import re
import spacy
import pytextrank

os.environ.setdefault('GIT_PYTHON_REFRESH', 'quiet')

_nlp = None

def get_nlp():
    """Get or initialize the spaCy NLP model with TextRank pipeline."""
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_md")
        except OSError:
            _nlp = spacy.load("en_core_web_sm")
        _nlp.add_pipe("textrank")
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

