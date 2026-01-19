from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from clubs.models import Club
from memberships.decorators import club_member_required
from memberships.helpers import get_membership, is_club_moderator
from .models import Post, PostType, Like, Comment
from .forms import BlogPostForm, NewsPostForm
from .utils.summarizer import summarize_text


def post_detail(request, slug, post_id):
    """Display a single post - accessible to everyone."""
    club = get_object_or_404(Club, slug=slug)
    post = get_object_or_404(Post, id=post_id, club=club, is_published=True)
    membership = get_membership(request.user, club)
    can_delete = membership and membership.role in ['admin', 'moderator']
    
    # Like/comment data
    is_liked = post.is_liked_by(request.user)
    comments = post.comments.select_related('user').all()
    
    return render(request, 'posts/post_detail.html', {
        'club': club,
        'post': post,
        'membership': membership,
        'can_delete': can_delete,
        'is_liked': is_liked,
        'like_count': post.like_count,
        'comments': comments,
        'comment_count': post.comment_count,
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
    
    # Get user's liked post IDs for efficient template rendering
    user_liked_post_ids = set()
    if request.user.is_authenticated:
        user_liked_post_ids = set(
            Like.objects.filter(
                user=request.user,
                post__in=news_posts
            ).values_list('post_id', flat=True)
        )

    return render(request, 'posts/post_list.html', {
        'club': club,
        'posts': news_posts,
        'list_type': 'news',
        'membership': membership,
        'user_liked_post_ids': user_liked_post_ids,
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
    
    # Get user's liked post IDs for efficient template rendering
    user_liked_post_ids = set()
    if request.user.is_authenticated:
        user_liked_post_ids = set(
            Like.objects.filter(
                user=request.user,
                post__in=blog_posts
            ).values_list('post_id', flat=True)
        )

    return render(request, 'posts/post_list.html', {
        'club': club,
        'posts': blog_posts,
        'list_type': 'blog',
        'membership': membership,
        'user_liked_post_ids': user_liked_post_ids,
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
            
            # Auto-summarize the post after creation (non-blocking - runs in background)
            # If user clicks "AI Summarize" before this completes, summarize_post view will handle it
            try:
                import logging
                import threading
                logger = logging.getLogger(__name__)
                
                def generate_summary_async():
                    """Generate summary in background thread."""
                    try:
                        # Refresh post from DB to ensure we have latest data
                        post_refreshed = Post.objects.get(id=post.id)
                        logger.info(f"Auto-summarizing post {post_refreshed.id} on creation (background)")
                        summary = summarize_text(post_refreshed.body)
                        if summary:
                            post_refreshed.summary = summary
                            post_refreshed.save(update_fields=['summary'])
                            logger.info(f"Summary generated and saved for post {post_refreshed.id}")
                        else:
                            logger.warning(f"Summarization returned empty result for post {post_refreshed.id}")
                    except Exception as e:
                        logger.error(f"Failed to auto-summarize post {post.id} in background: {e}", exc_info=True)
                
                # Start summarization in background thread (non-blocking)
                thread = threading.Thread(target=generate_summary_async, daemon=True)
                thread.start()
                logger.info(f"Started background summarization for post {post.id}")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to start background summarization for post {post.id}: {e}", exc_info=True)
                # Continue even if background thread fails - post is already saved
            
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
    """Summarize a post using Hugging Face transformers - returns HTML fragment for HTMX.
    Uses cached summary from database if available, otherwise generates and stores it.
    """
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
    
    # Check if summary exists in database (cached)
    if post.summary:
        logger.info(f"Using cached summary for post {post_id}")
        return render(request, 'posts/partials/post_content.html', {
            'club': club,
            'post': post,
            'summary': post.summary,
            'is_summarized': True,
        })
    
    # Generate summary on-demand if not cached
    try:
        logger.info(f"Generating summary for post {post_id} (not cached)")
        summary = summarize_text(post.body)
        if not summary:
            raise ValueError("Summarization returned empty result")
        
        # Store the generated summary in the database for future use
        post.summary = summary
        post.save(update_fields=['summary'])
        logger.info(f"Summary generated and cached for post {post_id}")
        
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
            'error': 'Summarization library not available. Please install transformers and torch.',
        })
    except OSError as e:
        logger.error(f"OS error during summarization: {e}")
        summary = post.body[:300] + "..." if len(post.body) > 300 else post.body
        return render(request, 'posts/partials/post_content.html', {
            'club': club,
            'post': post,
            'summary': summary,
            'is_summarized': True,
            'is_fallback': True,
            'error': f'Summarization failed: {str(e)}',
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


@require_http_methods(["POST"])
@club_member_required
def toggle_like(request, slug, post_id):
    """Toggle like on a post - members only. Returns HTML fragment for HTMX."""
    club = get_object_or_404(Club, slug=slug)
    post = get_object_or_404(Post, id=post_id, club=club, is_published=True)
    
    # Check if user already liked
    existing_like = Like.objects.filter(post=post, user=request.user).first()
    
    if existing_like:
        existing_like.delete()
        is_liked = False
    else:
        Like.objects.create(post=post, user=request.user)
        is_liked = True
    
    # Return updated like button partial
    return render(request, 'posts/partials/like_button.html', {
        'post': post,
        'club': club,
        'is_liked': is_liked,
        'like_count': post.like_count,
    })


@require_http_methods(["POST"])
@club_member_required
def add_comment(request, slug, post_id):
    """Add a comment to a post - members only. Returns HTML fragment for HTMX."""
    club = get_object_or_404(Club, slug=slug)
    post = get_object_or_404(Post, id=post_id, club=club, is_published=True)
    
    body = request.POST.get('body', '').strip()
    
    if not body:
        messages.error(request, 'Comment cannot be empty.')
        return render(request, 'posts/partials/comment_form.html', {
            'post': post,
            'club': club,
            'error': 'Comment cannot be empty.',
        })
    
    comment = Comment.objects.create(
        post=post,
        user=request.user,
        body=body
    )
    
    # Return the new comment and updated form
    return render(request, 'posts/partials/comment_added.html', {
        'post': post,
        'club': club,
        'comment': comment,
        'membership': get_membership(request.user, club),
    })


@require_http_methods(["POST"])
@club_member_required
def delete_comment(request, slug, post_id, comment_id):
    """Delete a comment - only comment author or moderators/admins can delete."""
    club = get_object_or_404(Club, slug=slug)
    post = get_object_or_404(Post, id=post_id, club=club, is_published=True)
    comment = get_object_or_404(Comment, id=comment_id, post=post)
    membership = get_membership(request.user, club)
    
    # Check permission: comment author or moderator/admin
    can_delete = (
        comment.user == request.user or 
        (membership and membership.role in ['admin', 'moderator'])
    )
    
    if not can_delete:
        return render(request, 'posts/partials/comment_item.html', {
            'comment': comment,
            'club': club,
            'post': post,
            'membership': membership,
            'error': 'You do not have permission to delete this comment.',
        })
    
    comment.delete()
    
    # Return empty response (comment will be removed from DOM)
    return render(request, 'posts/partials/comment_deleted.html', {
        'post': post,
    })
