from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from clubs.models import Club
from memberships.decorators import club_member_required
from memberships.helpers import get_membership, is_club_moderator
from .models import Post, PostType
from .forms import BlogPostForm, NewsPostForm


def post_detail(request, slug, post_id):
    """Display a single post - accessible to everyone."""
    club = get_object_or_404(Club, slug=slug)
    post = get_object_or_404(Post, id=post_id, club=club, is_published=True)
    
    return render(request, 'posts/post_detail.html', {
        'club': club,
        'post': post,
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
    
    # Check permissions (re-check on every request to handle role changes)
    can_create_news = is_club_moderator(request.user, club)
    
    # Choose form based on role
    FormClass = NewsPostForm if can_create_news else BlogPostForm
    
    # Get initial post type from URL parameter (for moderators/admins only)
    initial = {}
    if can_create_news:
        url_type = request.GET.get('type', '').lower()
        if url_type == 'news':
            initial['post_type'] = PostType.NEWS
    
    if request.method == 'POST':
        # CRITICAL: Re-check permissions at submission time (handles role changes during form fill)
        can_create_news_now = is_club_moderator(request.user, club)
        
        # Check raw POST data for post_type (even if form class changed)
        raw_post_type = request.POST.get('post_type', '').strip()
        
        # Security check: If user selected NEWS but is no longer moderator, reject immediately
        if raw_post_type == PostType.NEWS and not can_create_news_now:
            messages.error(
                request, 
                'You do not have permission to create News posts. Only moderators and admins can create News posts.'
            )
            # Re-render with appropriate form class based on current role
            FormClassNow = NewsPostForm if can_create_news_now else BlogPostForm
            form = FormClassNow(request.POST)
            return render(request, 'posts/post_create.html', {
                'form': form,
                'club': club,
                'membership': membership,
                'can_create_news': can_create_news_now,
            })
        
        # Use correct form class based on current permissions
        FormClassNow = NewsPostForm if can_create_news_now else BlogPostForm
        form = FormClassNow(request.POST)
        
        if form.is_valid():
            post = form.save(commit=False)
            post.club = club
            post.author = request.user
            
            # Final security check: Ensure members can't create NEWS
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
            
            # For members, always set to BLOG (safety check)
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
