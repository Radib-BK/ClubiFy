from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from clubs.models import Club
from memberships.decorators import club_member_required
from memberships.helpers import get_membership, is_club_moderator
from .models import Post, PostType
from .forms import BlogPostForm, NewsPostForm
from .utils.summarizer import summarize_text


def post_detail(request, slug, post_id):
    """Display a single post - accessible to everyone."""
    club = get_object_or_404(Club, slug=slug)
    post = get_object_or_404(Post, id=post_id, club=club, is_published=True)
    membership = get_membership(request.user, club)
    can_delete = membership and membership.role in ['admin', 'moderator']
    
    return render(request, 'posts/post_detail.html', {
        'club': club,
        'post': post,
        'membership': membership,
        'can_delete': can_delete,
    })


@club_member_required
def news_list(request, slug):
    """List all news posts for a club - members only."""
    club = get_object_or_404(Club, slug=slug)
    membership = get_membership(request.user, club)

    news_posts = Post.objects.filter(
        club=club,
        post_type=PostType.NEWS,
        is_published=True,
    ).order_by('-created_at')

    return render(request, 'posts/post_list.html', {
        'club': club,
        'posts': news_posts,
        'list_type': 'news',
        'membership': membership,
    })


@club_member_required
def blog_list(request, slug):
    """List all blog posts for a club - members only."""
    club = get_object_or_404(Club, slug=slug)
    membership = get_membership(request.user, club)

    blog_posts = Post.objects.filter(
        club=club,
        post_type=PostType.BLOG,
        is_published=True,
    ).order_by('-created_at')

    return render(request, 'posts/post_list.html', {
        'club': club,
        'posts': blog_posts,
        'list_type': 'blog',
        'membership': membership,
    })


@club_member_required
def create_post(request, slug):
    """Create a new post - members can create blogs, moderators/admins can create news."""
    club = get_object_or_404(Club, slug=slug)
    membership = get_membership(request.user, club)
    
    if not membership:
        messages.error(request, 'You must be a member of this club to create posts.')
        return redirect('clubs:club_detail', slug=slug)
    
    can_create_news = is_club_moderator(request.user, club)
    FormClass = NewsPostForm if can_create_news else BlogPostForm
    
    initial = {}
    if can_create_news:
        url_type = request.GET.get('type', '').lower()
        if url_type == 'news':
            initial['post_type'] = PostType.NEWS
    
    if request.method == 'POST':
        can_create_news_now = is_club_moderator(request.user, club)
        raw_post_type = request.POST.get('post_type', '').strip()
        
        if raw_post_type == PostType.NEWS and not can_create_news_now:
            messages.error(
                request, 
                'You do not have permission to create News posts. Only moderators and admins can create News posts.'
            )
            FormClassNow = NewsPostForm if can_create_news_now else BlogPostForm
            form = FormClassNow(request.POST)
            return render(request, 'posts/post_create.html', {
                'form': form,
                'club': club,
                'membership': membership,
                'can_create_news': can_create_news_now,
            })
        
        FormClassNow = NewsPostForm if can_create_news_now else BlogPostForm
        form = FormClassNow(request.POST)
        
        if form.is_valid():
            post = form.save(commit=False)
            post.club = club
            post.author = request.user
            
            if post.post_type == PostType.NEWS and not can_create_news_now:
                messages.error(
                    request, 
                    'You do not have permission to create News posts. Only moderators and admins can create News posts.'
                )
                form = FormClassNow(request.POST)
                return render(request, 'posts/post_create.html', {
                    'form': form,
                    'club': club,
                    'membership': membership,
                    'can_create_news': can_create_news_now,
                })
            
            if not can_create_news_now:
                post.post_type = PostType.BLOG
            
            post.save()
            post_type_display = 'News' if post.is_news else 'Blog'
            messages.success(request, f'{post_type_display} post "{post.title}" created successfully!')
            return redirect('clubs:club_detail', slug=slug)
    else:
        form = FormClass(initial=initial)
    
    return render(request, 'posts/post_create.html', {
        'form': form,
        'club': club,
        'membership': membership,
        'can_create_news': can_create_news,
    })


@club_member_required
def delete_post(request, slug, post_id):
    """Delete a post - moderators and admins only."""
    club = get_object_or_404(Club, slug=slug)
    post = get_object_or_404(Post, id=post_id, club=club, is_published=True)
    membership = get_membership(request.user, club)
    
    if not membership or membership.role not in ['admin', 'moderator']:
        messages.error(request, 'You do not have permission to delete posts. Only moderators and admins can delete posts.')
        return redirect('posts:post_detail', slug=slug, post_id=post_id)
    
    post_title = post.title
    post.delete()
    messages.success(request, f'Post "{post_title}" has been deleted.')
    return redirect('clubs:club_detail', slug=slug)


@require_http_methods(["POST"])
def summarize_post(request, slug, post_id):
    """Summarize a post using Hugging Face transformers with fallback to spaCy and PyTextRank - returns HTML fragment for HTMX."""
    import logging
    logger = logging.getLogger(__name__)
    
    club = get_object_or_404(Club, slug=slug)
    post = get_object_or_404(Post, id=post_id, club=club, is_published=True)
    action = request.POST.get('action', 'summarize')
    
    if action == 'original':
        return render(request, 'posts/partials/post_content.html', {
            'club': club,
            'post': post,
            'is_summarized': False,
        })
    
    try:
        logger.info(f"Starting summarization for post {post_id}")
        summary = summarize_text(post.body)
        if not summary:
            raise ValueError("Summarization returned empty result")
        logger.info(f"Summarization completed successfully for post {post_id}")
        return render(request, 'posts/partials/post_content.html', {
            'club': club,
            'post': post,
            'summary': summary,
            'is_summarized': True,
        })
    except ImportError as e:
        logger.error(f"Import error during summarization: {e}")
        summary = post.body[:300] + "..." if len(post.body) > 300 else post.body
        return render(request, 'posts/partials/post_content.html', {
            'club': club,
            'post': post,
            'summary': summary,
            'is_summarized': True,
            'is_fallback': True,
            'error': 'Summarization library not available. Please install transformers, torch, spacy and PyTextRank.',
        })
    except OSError as e:
        logger.error(f"OS error during summarization: {e}")
        summary = post.body[:300] + "..." if len(post.body) > 300 else post.body
        model_name = 'en_core_web_md' if 'md' in str(e) else 'en_core_web_sm'
        return render(request, 'posts/partials/post_content.html', {
            'club': club,
            'post': post,
            'summary': summary,
            'is_summarized': True,
            'is_fallback': True,
            'error': f'Language model not found. Please download: python -m spacy download {model_name}',
        })
    except Exception as e:
        logger.error(f"Error during summarization: {e}", exc_info=True)
        summary = post.body[:300] + "..." if len(post.body) > 300 else post.body
        return render(request, 'posts/partials/post_content.html', {
            'club': club,
            'post': post,
            'summary': summary,
            'is_summarized': True,
            'is_fallback': True,
            'error': f'Error during summarization: {str(e)}',
        })
