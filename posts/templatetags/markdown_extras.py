"""
Custom template filters for Markdown rendering.
"""
import markdown
import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

_LIST_LINE_RE = re.compile(r'^\s*([\*\+-]\s|\d+\.\s)')


def _ensure_blank_before_lists(text):
    """Insert a blank line before lists when needed for proper markdown parsing."""
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


def _convert_html_tables_to_markdown(text):
    """Convert HTML tables to markdown table syntax."""
    def convert_table(match):
        table_html = match.group(1)
        markdown_rows = []
        
        # Extract header row
        header_match = re.search(r'<thead[^>]*>.*?<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
        if not header_match:
            header_match = re.search(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
            if not (header_match and '<th' in header_match.group(1)):
                header_match = None
        
        if header_match:
            header_cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', header_match.group(1), re.DOTALL)
            headers = [re.sub(r'<[^>]+>', '', cell).strip() for cell in header_cells]
            if headers:
                markdown_rows.append('| ' + ' | '.join(headers) + ' |')
                markdown_rows.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
        
        # Extract body rows
        body_match = re.search(r'<tbody[^>]*>(.*?)</tbody>', table_html, re.DOTALL)
        body_content = body_match.group(1) if body_match else table_html
        
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', body_content, re.DOTALL)
        for row in rows:
            if '<th' in row and header_match:
                continue
            cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL)
            cell_texts = [re.sub(r'<[^>]+>', '', cell).strip() for cell in cells]
            if cell_texts:
                markdown_rows.append('| ' + ' | '.join(cell_texts) + ' |')
        
        return '\n' + '\n'.join(markdown_rows) + '\n' if markdown_rows else match.group(0)
    
    return re.sub(r'<table[^>]*>(.*?)</table>', convert_table, text, flags=re.DOTALL | re.IGNORECASE)


def _normalize_tables(text):
    """Normalize table markdown to ensure proper PHP Markdown Extra format."""
    if not text:
        return text
    
    lines = text.split('\n')
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        if '|' in line and stripped.startswith('|') and stripped.endswith('|'):
            table_rows = [line]
            i += 1
            has_separator = False
            
            # Check for separator row
            if i < len(lines):
                next_line = lines[i]
                if '|' in next_line and ('---' in next_line or '===' in next_line or 
                                        all(c in '-=|: ' for c in next_line.strip().replace('|', ''))):
                    table_rows.append(next_line)
                    has_separator = True
                    i += 1
            
            # Collect remaining table rows
            while i < len(lines):
                next_line = lines[i]
                if '|' in next_line and next_line.strip().startswith('|') and next_line.strip().endswith('|'):
                    table_rows.append(next_line)
                    i += 1
                else:
                    break
            
            # Insert separator if missing
            if len(table_rows) >= 2 and not has_separator:
                col_count = table_rows[0].count('|') - 1
                if col_count > 0:
                    separator = '|' + '|'.join(['---'] * col_count) + '|'
                    table_rows.insert(1, separator)
            
            if len(table_rows) >= 3:
                result.extend(table_rows)
                if i < len(lines) and lines[i].strip():
                    result.append('')
                continue
        
        result.append(line)
        i += 1
    
    return '\n'.join(result)


@register.filter(name='markdown')
def markdown_filter(text):
    """Convert Markdown text to HTML with table support."""
    if not text:
        return ''
    
    text = str(text)
    text = _convert_html_tables_to_markdown(text)
    text = _normalize_tables(text)
    text = _ensure_blank_before_lists(text)
    
    md = markdown.Markdown(
        extensions=['extra', 'codehilite', 'nl2br', 'sane_lists'],
        extension_configs={'codehilite': {'css_class': 'highlight', 'use_pygments': False}}
    )
    
    return mark_safe(md.convert(text))


@register.filter(name='markdown_to_text')
def markdown_to_text(text):
    """Convert Markdown to plain text by stripping all markdown syntax."""
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
    """Check if a value is in a collection (list, set, tuple)."""
    if collection is None:
        return False
    return value in collection
