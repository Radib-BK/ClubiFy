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
def create_post(request, slug):
    """Create a new post - members can create blogs, moderators/admins can create news."""
    club = get_object_or_404(Club, slug=slug)
    membership = get_membership(request.user, club)
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
        form = FormClass(request.POST)
        
        if form.is_valid():
            post = form.save(commit=False)
            post.club = club
            post.author = request.user
            
            # For members, always set to BLOG
            if not can_create_news:
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
