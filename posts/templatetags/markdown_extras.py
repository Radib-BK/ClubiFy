"""
Custom template filters for Markdown rendering.
"""
import markdown
import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# List line: starts with * - + (optional leading space) or 1. 2. etc.
_LIST_LINE_RE = re.compile(r'^\s*([\*\+-]\s|\d+\.\s)')


def _ensure_blank_before_lists(text):
    """
    Insert a blank line before a list when the previous line is non-blank and
    not itself a list. Markdown requires a blank line before block-level lists
    when they follow a paragraph (e.g. "Test:\n* item" does not parse as a list).
    """
    if not text:
        return text
    lines = text.split('\n')
    result = []
    for i, line in enumerate(lines):
        if i > 0 and _LIST_LINE_RE.match(line):
            prev = lines[i - 1]
            if prev.strip() and not _LIST_LINE_RE.match(prev):
                result.append('')
        result.append(line)
    return '\n'.join(result)


@register.filter(name='markdown')
def markdown_filter(text):
    """
    Convert Markdown text to HTML.
    Supports common Markdown features: headers, lists, links, bold, italic, code blocks.
    """
    if not text:
        return ''
    
    text = _ensure_blank_before_lists(str(text))
    
    md = markdown.Markdown(
        extensions=[
            'extra',
            'codehilite',
            'nl2br',
            'sane_lists',
        ],
        extension_configs={
            'codehilite': {
                'css_class': 'highlight',
                'use_pygments': False,
            }
        }
    )
    
    html = md.convert(text)
    return mark_safe(html)


@register.filter(name='markdown_to_text')
def markdown_to_text(text):
    """
    Convert Markdown to plain text by stripping all markdown syntax.
    Useful for previews and excerpts.
    """
    if not text:
        return ''
    
    text = str(text)
    
    text = re.sub(r'#{1,6}\s+', '', text)
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'^[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    
    return text


@register.filter(name='in_set')
def in_set(value, collection):
    """
    Check if a value is in a collection (list, set, tuple).
    Usage: {{ post.id|in_set:user_liked_post_ids }}
    """
    if collection is None:
        return False
    return value in collection

