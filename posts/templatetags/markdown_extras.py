"""
Custom template filters for Markdown rendering.
"""
import markdown
import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='markdown')
def markdown_filter(text):
    """
    Convert Markdown text to HTML.
    Supports common Markdown features: headers, lists, links, bold, italic, code blocks.
    """
    if not text:
        return ''
    
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

