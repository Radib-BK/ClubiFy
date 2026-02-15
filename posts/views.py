from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control

from clubs.models import Club
from memberships.decorators import club_member_required
from memberships.helpers import get_membership, is_club_moderator
from .models import Post, PostType, Like, Comment, Bookmark
from .forms import BlogPostForm, NewsPostForm
from .utils.summarizer import summarize_text


def post_detail(request, slug, post_id):
    """Display a single post - accessible to everyone."""
    club = get_object_or_404(Club, slug=slug)
    post = get_object_or_404(Post, id=post_id, club=club, is_published=True)
    membership = get_membership(request.user, club)
    can_delete = membership and membership.role in ["admin", "moderator"]
    can_edit = request.user.is_authenticated and post.author == request.user

    # Like/comment/bookmark data
    is_liked = post.is_liked_by(request.user)
    is_bookmarked = False
    if request.user.is_authenticated:
        is_bookmarked = Bookmark.objects.filter(post=post, user=request.user).exists()
    comments = post.comments.select_related("user").all()

    return render(
        request,
        "posts/post_detail.html",
        {
            "club": club,
            "post": post,
            "membership": membership,
            "can_delete": can_delete,
            "can_edit": can_edit,
            "is_liked": is_liked,
            "is_bookmarked": is_bookmarked,
            "like_count": post.like_count,
            "comments": comments,
            "comment_count": post.comment_count,
        },
    )


@club_member_required
def news_list(request, slug):
    """List all news posts for a club - members only."""
    club = get_object_or_404(Club, slug=slug)
    membership = get_membership(request.user, club)
    can_create_news = is_club_moderator(request.user, club)

    news_posts = Post.objects.filter(
        club=club,
        post_type=PostType.NEWS,
        is_published=True,
    ).order_by("-created_at")

    # Get user's liked post IDs for efficient template rendering
    user_liked_post_ids = set()
    if request.user.is_authenticated:
        user_liked_post_ids = set(
            Like.objects.filter(user=request.user, post__in=news_posts).values_list(
                "post_id", flat=True
            )
        )

    return render(
        request,
        "posts/post_list.html",
        {
            "club": club,
            "posts": news_posts,
            "list_type": "news",
            "membership": membership,
            "can_create_news": can_create_news,
            "user_liked_post_ids": user_liked_post_ids,
        },
    )


@club_member_required
def blog_list(request, slug):
    """List all blog posts for a club - members only."""
    club = get_object_or_404(Club, slug=slug)
    membership = get_membership(request.user, club)
    can_create_news = is_club_moderator(request.user, club)

    blog_posts = Post.objects.filter(
        club=club,
        post_type=PostType.BLOG,
        is_published=True,
    ).order_by("-created_at")

    # Get user's liked post IDs for efficient template rendering
    user_liked_post_ids = set()
    if request.user.is_authenticated:
        user_liked_post_ids = set(
            Like.objects.filter(user=request.user, post__in=blog_posts).values_list(
                "post_id", flat=True
            )
        )

    return render(
        request,
        "posts/post_list.html",
        {
            "club": club,
            "posts": blog_posts,
            "list_type": "blog",
            "membership": membership,
            "can_create_news": can_create_news,
            "user_liked_post_ids": user_liked_post_ids,
        },
    )


@club_member_required
def create_post(request, slug):
    """Create a new post - members can create blogs, moderators/admins can create news."""
    club = get_object_or_404(Club, slug=slug)
    membership = get_membership(request.user, club)

    if not membership:
        messages.error(request, "You must be a member of this club to create posts.")
        return redirect("clubs:club_detail", slug=slug)

    can_create_news = is_club_moderator(request.user, club)
    FormClass = NewsPostForm if can_create_news else BlogPostForm

    initial = {}
    if can_create_news:
        url_type = request.GET.get("type", "").lower()
        if url_type == "news":
            initial["post_type"] = PostType.NEWS

    if request.method == "POST":
        can_create_news_now = is_club_moderator(request.user, club)
        raw_post_type = request.POST.get("post_type", "").strip()

        if raw_post_type == PostType.NEWS and not can_create_news_now:
            messages.error(
                request,
                "You do not have permission to create News posts. Only moderators and admins can create News posts.",
            )
            FormClassNow = NewsPostForm if can_create_news_now else BlogPostForm
            form = FormClassNow(request.POST)
            return render(
                request,
                "posts/post_create.html",
                {
                    "form": form,
                    "club": club,
                    "membership": membership,
                    "can_create_news": can_create_news_now,
                },
            )

        FormClassNow = NewsPostForm if can_create_news_now else BlogPostForm
        form = FormClassNow(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            post.club = club
            post.author = request.user

            if post.post_type == PostType.NEWS and not can_create_news_now:
                messages.error(
                    request,
                    "You do not have permission to create News posts. Only moderators and admins can create News posts.",
                )
                form = FormClassNow(request.POST)
                return render(
                    request,
                    "posts/post_create.html",
                    {
                        "form": form,
                        "club": club,
                        "membership": membership,
                        "can_create_news": can_create_news_now,
                    },
                )

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
                        logger.info(
                            f"Auto-summarizing post {post_refreshed.id} on creation (background)"
                        )
                        summary = summarize_text(post_refreshed.body)
                        if summary:
                            post_refreshed.summary = summary
                            post_refreshed.save(update_fields=["summary"])
                            logger.info(
                                f"Summary generated and saved for post {post_refreshed.id}"
                            )
                        else:
                            logger.warning(
                                f"Summarization returned empty result for post {post_refreshed.id}"
                            )
                    except Exception as e:
                        logger.error(
                            f"Failed to auto-summarize post {post.id} in background: {e}",
                            exc_info=True,
                        )

                # Start summarization in background thread (non-blocking)
                thread = threading.Thread(target=generate_summary_async, daemon=True)
                thread.start()
                logger.info(f"Started background summarization for post {post.id}")
            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.error(
                    f"Failed to start background summarization for post {post.id}: {e}",
                    exc_info=True,
                )
                # Continue even if background thread fails - post is already saved

            post_type_display = "News" if post.is_news else "Blog"
            messages.success(
                request,
                f'{post_type_display} post "{post.title}" created successfully!',
            )
            return redirect("clubs:club_detail", slug=slug)
    else:
        form = FormClass(initial=initial)

    return render(
        request,
        "posts/post_create.html",
        {
            "form": form,
            "club": club,
            "membership": membership,
            "can_create_news": can_create_news,
        },
    )


@club_member_required
def edit_post(request, slug, post_id):
    """Edit a post - only the post creator can edit."""
    club = get_object_or_404(Club, slug=slug)
    post = get_object_or_404(Post, id=post_id, club=club, is_published=True)
    membership = get_membership(request.user, club)

    # Check if user is the post author
    if post.author != request.user:
        messages.error(
            request,
            "You do not have permission to edit this post. Only the post creator can edit posts.",
        )
        return redirect("posts:post_detail", slug=slug, post_id=post_id)

    can_create_news = is_club_moderator(request.user, club)
    FormClass = NewsPostForm if can_create_news else BlogPostForm

    if request.method == "POST":
        can_create_news_now = is_club_moderator(request.user, club)
        raw_post_type = request.POST.get("post_type", "").strip()

        # If trying to change to News but not allowed, prevent it
        if raw_post_type == PostType.NEWS and not can_create_news_now:
            messages.error(
                request,
                "You do not have permission to change this post to News. Only moderators and admins can create News posts.",
            )
            FormClassNow = NewsPostForm if can_create_news_now else BlogPostForm
            form = FormClassNow(request.POST, instance=post)
            return render(
                request,
                "posts/post_edit.html",
                {
                    "form": form,
                    "club": club,
                    "post": post,
                    "membership": membership,
                    "can_create_news": can_create_news_now,
                },
            )

        FormClassNow = NewsPostForm if can_create_news_now else BlogPostForm
        form = FormClassNow(request.POST, instance=post)

        if form.is_valid():
            updated_post = form.save(commit=False)

            # Prevent changing post type to News if not allowed
            if updated_post.post_type == PostType.NEWS and not can_create_news_now:
                messages.error(
                    request,
                    "You do not have permission to change this post to News. Only moderators and admins can create News posts.",
                )
                form = FormClassNow(request.POST, instance=post)
                return render(
                    request,
                    "posts/post_edit.html",
                    {
                        "form": form,
                        "club": club,
                        "post": post,
                        "membership": membership,
                        "can_create_news": can_create_news_now,
                    },
                )

            # If user can't create news, ensure post type remains Blog
            if not can_create_news_now:
                updated_post.post_type = PostType.BLOG

            # Keep the original author and club
            updated_post.author = post.author
            updated_post.club = club
            updated_post.save()

            post_type_display = "News" if updated_post.is_news else "Blog"
            messages.success(
                request,
                f'{post_type_display} post "{updated_post.title}" updated successfully!',
            )
            return redirect("posts:post_detail", slug=slug, post_id=post_id)
    else:
        form = FormClass(instance=post)

    return render(
        request,
        "posts/post_edit.html",
        {
            "form": form,
            "club": club,
            "post": post,
            "membership": membership,
            "can_create_news": can_create_news,
        },
    )


@club_member_required
def delete_post(request, slug, post_id):
    """Delete a post - moderators and admins only."""
    club = get_object_or_404(Club, slug=slug)
    post = get_object_or_404(Post, id=post_id, club=club, is_published=True)
    membership = get_membership(request.user, club)

    if not membership or membership.role not in ["admin", "moderator"]:
        messages.error(
            request,
            "You do not have permission to delete posts. Only moderators and admins can delete posts.",
        )
        return redirect("posts:post_detail", slug=slug, post_id=post_id)

    post_title = post.title
    post.delete()
    messages.success(request, f'Post "{post_title}" has been deleted.')
    return redirect("clubs:club_detail", slug=slug)


@require_http_methods(["POST"])
def summarize_post(request, slug, post_id):
    """Summarize a post using Hugging Face transformers - returns HTML fragment for HTMX.
    Uses cached summary from database if available, otherwise generates and stores it.
    """
    import logging

    logger = logging.getLogger(__name__)

    club = get_object_or_404(Club, slug=slug)
    post = get_object_or_404(Post, id=post_id, club=club, is_published=True)
    action = request.POST.get("action", "summarize")

    if action == "original":
        return render(
            request,
            "posts/partials/post_content.html",
            {
                "club": club,
                "post": post,
                "is_summarized": False,
            },
        )

    # Check if summary exists in database (cached)
    if post.summary:
        logger.info(f"Using cached summary for post {post_id}")
        return render(
            request,
            "posts/partials/post_content.html",
            {
                "club": club,
                "post": post,
                "summary": post.summary,
                "is_summarized": True,
            },
        )

    # Generate summary on-demand if not cached
    try:
        logger.info(f"Generating summary for post {post_id} (not cached)")
        summary = summarize_text(post.body)
        if not summary:
            raise ValueError("Summarization returned empty result")

        # Store the generated summary in the database for future use
        post.summary = summary
        post.save(update_fields=["summary"])
        logger.info(f"Summary generated and cached for post {post_id}")

        return render(
            request,
            "posts/partials/post_content.html",
            {
                "club": club,
                "post": post,
                "summary": summary,
                "is_summarized": True,
            },
        )
    except ImportError as e:
        logger.error(f"Import error during summarization: {e}")
        summary = post.body[:300] + "..." if len(post.body) > 300 else post.body
        return render(
            request,
            "posts/partials/post_content.html",
            {
                "club": club,
                "post": post,
                "summary": summary,
                "is_summarized": True,
                "is_fallback": True,
                "error": "Summarization library not available. Please install transformers and torch.",
            },
        )
    except OSError as e:
        logger.error(f"OS error during summarization: {e}")
        summary = post.body[:300] + "..." if len(post.body) > 300 else post.body
        return render(
            request,
            "posts/partials/post_content.html",
            {
                "club": club,
                "post": post,
                "summary": summary,
                "is_summarized": True,
                "is_fallback": True,
                "error": f"Summarization failed: {str(e)}",
            },
        )
    except Exception as e:
        logger.error(f"Error during summarization: {e}", exc_info=True)
        summary = post.body[:300] + "..." if len(post.body) > 300 else post.body
        return render(
            request,
            "posts/partials/post_content.html",
            {
                "club": club,
                "post": post,
                "summary": summary,
                "is_summarized": True,
                "is_fallback": True,
                "error": f"Error during summarization: {str(e)}",
            },
        )


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
    return render(
        request,
        "posts/partials/like_button.html",
        {
            "post": post,
            "club": club,
            "is_liked": is_liked,
            "like_count": post.like_count,
        },
    )


@require_http_methods(["POST"])
@login_required
def toggle_bookmark(request, slug, post_id):
    """Toggle bookmark on a post - authenticated users only."""
    club = get_object_or_404(Club, slug=slug)
    post = get_object_or_404(Post, id=post_id, club=club, is_published=True)

    # Check if user already bookmarked
    existing_bookmark = Bookmark.objects.filter(post=post, user=request.user).first()

    if existing_bookmark:
        existing_bookmark.delete()
        is_bookmarked = False
        messages.success(request, "Post removed from bookmarks.")
    else:
        Bookmark.objects.create(post=post, user=request.user)
        is_bookmarked = True
        messages.success(request, "Post bookmarked!")

    return redirect("posts:post_detail", slug=slug, post_id=post_id)


@require_http_methods(["POST"])
@club_member_required
def add_comment(request, slug, post_id):
    """Add a comment to a post - members only. Returns HTML fragment for HTMX."""
    club = get_object_or_404(Club, slug=slug)
    post = get_object_or_404(Post, id=post_id, club=club, is_published=True)

    body = request.POST.get("body", "").strip()

    if not body:
        messages.error(request, "Comment cannot be empty.")
        return render(
            request,
            "posts/partials/comment_form.html",
            {
                "post": post,
                "club": club,
                "error": "Comment cannot be empty.",
            },
        )

    comment = Comment.objects.create(post=post, user=request.user, body=body)

    # Return the new comment and updated form
    return render(
        request,
        "posts/partials/comment_added.html",
        {
            "post": post,
            "club": club,
            "comment": comment,
            "membership": get_membership(request.user, club),
        },
    )


@require_http_methods(["POST"])
@club_member_required
def delete_comment(request, slug, post_id, comment_id):
    """Delete a comment - only comment author or moderators/admins can delete."""
    club = get_object_or_404(Club, slug=slug)
    post = get_object_or_404(Post, id=post_id, club=club, is_published=True)
    comment = get_object_or_404(Comment, id=comment_id, post=post)
    membership = get_membership(request.user, club)

    # Check permission: comment author or moderator/admin
    can_delete = comment.user == request.user or (
        membership and membership.role in ["admin", "moderator"]
    )

    if not can_delete:
        return render(
            request,
            "posts/partials/comment_item.html",
            {
                "comment": comment,
                "club": club,
                "post": post,
                "membership": membership,
                "error": "You do not have permission to delete this comment.",
            },
        )

    comment.delete()

    # Return empty response (comment will be removed from DOM)
    return render(
        request,
        "posts/partials/comment_deleted.html",
        {
            "post": post,
        },
    )


@login_required
def bookmark_list(request):
    """Display all bookmarked posts for the current user."""
    bookmarks = (
        Bookmark.objects.filter(user=request.user)
        .select_related("post", "post__author", "post__club")
        .order_by("-created_at")
    )

    bookmarked_posts = [bookmark.post for bookmark in bookmarks]

    return render(
        request,
        "posts/bookmark_list.html",
        {
            "bookmarked_posts": bookmarked_posts,
            "bookmark_count": len(bookmarked_posts),
        },
    )


@cache_control(max_age=86400)  # Cache for 24 hours
def post_og_image(request, slug, post_id):
    """Generate Open Graph image for social media sharing.

    Creates a 1200x630 image with:
    - Club's pastel color as background
    - Club logo (or first letter) centered
    - Post title and club name as text
    """
    from PIL import Image, ImageDraw, ImageFont
    from io import BytesIO
    import os

    club = get_object_or_404(Club, slug=slug)
    post = get_object_or_404(Post, id=post_id, club=club, is_published=True)

    # OG image dimensions (Facebook/Twitter recommended)
    width, height = 1200, 630

    # Parse club color and create a lighter/pastel version
    club_color = club.color or "#6366F1"  # Default to indigo
    if club_color.startswith("#"):
        hex_color = club_color[1:]
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
    else:
        r, g, b = 99, 102, 241  # Default indigo

    # Create pastel version by mixing with white
    pastel_r = int(r + (255 - r) * 0.6)
    pastel_g = int(g + (255 - g) * 0.6)
    pastel_b = int(b + (255 - b) * 0.6)
    bg_color = (pastel_r, pastel_g, pastel_b)

    # Darker version for text
    dark_r = int(r * 0.7)
    dark_g = int(g * 0.7)
    dark_b = int(b * 0.7)
    text_color = (dark_r, dark_g, dark_b)

    # Create image
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Try to load fonts (use default if not available)
    try:
        # Try system fonts
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:\\Windows\\Fonts\\arial.ttf",
        ]
        title_font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                title_font = ImageFont.truetype(font_path, 48)
                subtitle_font = ImageFont.truetype(font_path, 28)
                logo_font = ImageFont.truetype(font_path, 120)
                break
        if not title_font:
            title_font = ImageFont.load_default()
            subtitle_font = title_font
            logo_font = title_font
    except Exception:
        title_font = ImageFont.load_default()
        subtitle_font = title_font
        logo_font = title_font

    # Draw club logo or letter in center
    center_x, center_y = width // 2, height // 2 - 40

    if club.logo:
        try:
            logo_path = club.logo.path
            logo_img = Image.open(logo_path)
            # Resize logo to fit
            logo_size = 180
            logo_img = logo_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            # Convert to RGBA if needed
            if logo_img.mode != "RGBA":
                logo_img = logo_img.convert("RGBA")
            # Create circular mask
            mask = Image.new("L", (logo_size, logo_size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, logo_size, logo_size), fill=255)
            # Paste logo with white background circle
            circle_bg = Image.new("RGBA", (logo_size, logo_size), (255, 255, 255, 255))
            img.paste(
                circle_bg,
                (center_x - logo_size // 2, center_y - logo_size // 2 - 30),
                mask,
            )
            img.paste(
                logo_img,
                (center_x - logo_size // 2, center_y - logo_size // 2 - 30),
                mask,
            )
        except Exception:
            # Fall back to letter logo
            _draw_letter_logo(
                draw,
                center_x,
                center_y - 30,
                club.name[0].upper(),
                logo_font,
                (r, g, b),
            )
    else:
        # Draw letter logo
        _draw_letter_logo(
            draw, center_x, center_y - 30, club.name[0].upper(), logo_font, (r, g, b)
        )

    # Draw post title (centered, below logo)
    title = post.title
    if len(title) > 60:
        title = title[:57] + "..."

    # Get text bounding box for centering
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) // 2
    title_y = center_y + 100
    draw.text((title_x, title_y), title, fill=text_color, font=title_font)

    # Draw club name and ClubiFy branding
    subtitle = f"{club.name} • ClubiFy"
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_x = (width - subtitle_width) // 2
    subtitle_y = title_y + 60
    draw.text(
        (subtitle_x, subtitle_y), subtitle, fill=(100, 100, 100), font=subtitle_font
    )

    # Save to bytes
    buffer = BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type="image/png")


def _draw_letter_logo(draw, center_x, center_y, letter, font, color):
    """Helper to draw a circular letter logo."""
    # Draw white circle background
    circle_radius = 90
    draw.ellipse(
        (
            center_x - circle_radius,
            center_y - circle_radius,
            center_x + circle_radius,
            center_y + circle_radius,
        ),
        fill=(255, 255, 255),
    )
    # Draw letter
    letter_bbox = draw.textbbox((0, 0), letter, font=font)
    letter_width = letter_bbox[2] - letter_bbox[0]
    letter_height = letter_bbox[3] - letter_bbox[1]
    letter_x = center_x - letter_width // 2
    letter_y = center_y - letter_height // 2 - 10
    draw.text((letter_x, letter_y), letter, fill=color, font=font)
