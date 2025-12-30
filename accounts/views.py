from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView
from django.urls import reverse_lazy

from .forms import SignUpForm, LoginForm
from memberships.models import Membership, MembershipRequest, RequestStatus


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('clubs:club_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Log the user in after signup
        login(self.request, self.object)
        messages.success(self.request, f'Welcome to ClubiFy, {self.object.username}!')
        return response

    def dispatch(self, request, *args, **kwargs):
        # Redirect authenticated users
        if request.user.is_authenticated:
            return redirect('clubs:club_list')
        return super().dispatch(request, *args, **kwargs)


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f'Welcome back, {form.get_user().username}!')
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'You have been logged out.')
        return super().dispatch(request, *args, **kwargs)


@login_required
def profile(request):
    """User profile page showing memberships and pending requests."""
    user = request.user
    
    # Get user's memberships
    memberships = Membership.objects.filter(user=user).select_related('club').order_by('-joined_at')
    
    # Get pending requests
    pending_requests = MembershipRequest.objects.filter(
        user=user,
        status=RequestStatus.PENDING
    ).select_related('club').order_by('-requested_at')
    
    # Count stats
    admin_count = memberships.filter(role='admin').count()
    post_count = user.posts.count()
    
    return render(request, 'accounts/profile.html', {
        'memberships': memberships,
        'pending_requests': pending_requests,
        'admin_count': admin_count,
        'post_count': post_count,
    })
