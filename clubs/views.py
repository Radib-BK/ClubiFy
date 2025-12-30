from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy

from .models import Club
from .forms import ClubForm


class ClubListView(ListView):
    """Display all clubs - accessible to everyone including guests."""
    model = Club
    template_name = 'clubs/club_list.html'
    context_object_name = 'clubs'
    paginate_by = 12


class ClubDetailView(DetailView):
    """Display club details - accessible to everyone including guests."""
    model = Club
    template_name = 'clubs/club_detail.html'
    context_object_name = 'club'
    slug_url_kwarg = 'slug'


class ClubCreateView(LoginRequiredMixin, CreateView):
    """Create a new club - requires login. Creator becomes admin."""
    model = Club
    form_class = ClubForm
    template_name = 'clubs/club_create.html'
    
    def form_valid(self, form):
        # Set the creator
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Note: In checkpoint 2.1, we'll also create a Membership here
        # to make the creator an admin of the club
        
        messages.success(
            self.request, 
            f'Club "{self.object.name}" created successfully! You are now the admin.'
        )
        return response
    
    def get_success_url(self):
        return self.object.get_absolute_url()

