from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Q
from django.core.exceptions import PermissionDenied

from .models import Club
from .forms import ClubForm
from memberships.models import Membership, MembershipRequest, RequestStatus
from memberships.helpers import is_club_moderator, is_club_admin
from posts.models import Post, PostType, Like


class ClubListView(ListView):
    """Display all clubs - accessible to everyone including guests."""
    model = Club
    template_name = 'clubs/club_list.html'
    context_object_name = 'clubs'
    paginate_by = 6

    def get_queryset(self):
        """
        Support partial-name / description search across ALL clubs.
        Search is applied before pagination so results are global, not page-limited.
        """
        qs = super().get_queryset()
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(description__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        """
        Expose current search term so the input can keep its value
        and pagination links can preserve the query.
        """
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '').strip()
        return context


class ClubDetailView(DetailView):
    """Display club details - accessible to everyone including guests."""
    model = Club
    template_name = 'clubs/club_detail.html'
    context_object_name = 'club'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        club = self.object
        user = self.request.user

        context['is_member'] = False
        context['membership'] = None
        context['pending_request'] = None
        context['member_count'] = club.memberships.count()
        context['display_members'] = []
        context['has_more_members'] = False
        context['can_create_news'] = False
        context['can_edit_club'] = False

        if user.is_authenticated:
            context['can_edit_club'] = is_club_admin(user, club)
            membership = Membership.objects.filter(user=user, club=club).first()
            if membership:
                context['is_member'] = True
                context['membership'] = membership
                context['display_members'] = club.memberships.select_related('user')[:4]
                context['has_more_members'] = club.memberships.count() > 4
                context['can_create_news'] = is_club_moderator(user, club)
                context['can_edit_club'] = is_club_admin(user, club)

            pending = MembershipRequest.objects.filter(
                user=user, 
                club=club, 
                status=RequestStatus.PENDING
            ).first()
            context['pending_request'] = pending

        news_qs = Post.objects.filter(
            club=club, 
            post_type=PostType.NEWS,
            is_published=True
        ).order_by('-created_at')
        blog_qs = Post.objects.filter(
            club=club, 
            post_type=PostType.BLOG,
            is_published=True
        ).order_by('-created_at')

        context['news_total'] = news_qs.count()
        context['blog_total'] = blog_qs.count()
        context['news_posts'] = news_qs[:3]
        context['blog_posts'] = blog_qs[:3]
        
        # Get user's liked post IDs for the displayed posts
        user_liked_post_ids = set()
        if user.is_authenticated:
            all_displayed_posts = list(context['news_posts']) + list(context['blog_posts'])
            if all_displayed_posts:
                user_liked_post_ids = set(
                    Like.objects.filter(
                        user=user,
                        post__in=all_displayed_posts
                    ).values_list('post_id', flat=True)
                )
        context['user_liked_post_ids'] = user_liked_post_ids
        
        pending_requests_count = MembershipRequest.objects.filter(
            club=club,
            status=RequestStatus.PENDING
        ).count()
        context['pending_requests_count'] = pending_requests_count

        return context


class ClubCreateView(LoginRequiredMixin, CreateView):
    """Create a new club - requires login. Creator becomes admin."""
    model = Club
    form_class = ClubForm
    template_name = 'clubs/club_create.html'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(
            self.request, 
            f'Club "{self.object.name}" created successfully! You are now the admin.'
        )
        return response
    
    def get_success_url(self):
        return self.object.get_absolute_url()


class ClubUpdateView(LoginRequiredMixin, UpdateView):
    """Update club info - admin only."""
    model = Club
    form_class = ClubForm
    template_name = 'clubs/club_edit.html'
    context_object_name = 'club'
    slug_url_kwarg = 'slug'

    def get_object(self, queryset=None):
        club = super().get_object(queryset)
        if not is_club_admin(self.request.user, club):
            raise PermissionDenied("You must be a club admin to edit this club.")
        return club

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.setdefault('disable_name', True)
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Club "{self.object.name}" was updated successfully.')
        return response

    def get_success_url(self):
        return self.object.get_absolute_url()
