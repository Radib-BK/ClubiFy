"""
Test script for the summarization feature.
"""

import os
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "clubify.settings")
django.setup()

from posts.utils.summarizer import summarize_with_hf

# Test text - a sample article about Django
test_text = """
Django is a high-level Python web framework that encourages rapid development 
and clean, pragmatic design. Built by experienced developers, it takes care of 
much of the hassle of web development, so you can focus on writing your app 
without needing to reinvent the wheel. It's free and open source.

Django was designed to help developers take applications from concept to 
completion as quickly as possible. Django takes security seriously and helps 
developers avoid many common security mistakes. Some of the busiest sites on 
the web leverage Django's ability to quickly and flexibly scale.

The framework includes an ORM (Object-Relational Mapping) that allows developers 
to interact with databases using Python code instead of SQL. It also provides 
an automatic admin interface, URL routing, template system, and form handling. 
Django follows the model-template-view (MTV) architectural pattern, which is 
similar to the model-view-controller (MVC) pattern used by other frameworks.
"""

print("Testing summarization...")
print("=" * 80)
print(f"Original text length: {len(test_text)} characters")
print("=" * 80)

try:
    summary = summarize_with_hf(test_text, max_length=100, min_length=30)

    if summary:
        print("\n✓ Summarization successful!")
        print("=" * 80)
        print("SUMMARY:")
        print(summary)
        print("=" * 80)
        print(f"Summary length: {len(summary)} characters")
    else:
        print("\n✗ Summarization returned None")
        print("Check the logs for errors")

except Exception as e:
    print(f"\n✗ Error during summarization: {e}")
    import traceback

    traceback.print_exc()
