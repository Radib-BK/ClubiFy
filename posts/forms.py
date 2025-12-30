from django import forms
from .models import Post, PostType


class BlogPostForm(forms.ModelForm):
    """Form for regular members - Blog posts only."""
    
    class Meta:
        model = Post
        fields = ['title', 'body']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Enter post title'
            }),
            'body': forms.Textarea(attrs={
                'class': 'input',
                'rows': 10,
                'placeholder': 'Write your blog post here...'
            }),
        }


class NewsPostForm(forms.ModelForm):
    """Form for moderators/admins - can choose Blog or News."""
    
    class Meta:
        model = Post
        fields = ['post_type', 'title', 'body']
        widgets = {
            'post_type': forms.Select(attrs={
                'class': 'input',
            }),
            'title': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Enter post title'
            }),
            'body': forms.Textarea(attrs={
                'class': 'input',
                'rows': 10,
                'placeholder': 'Write your post content here...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['post_type'].choices = [
            (PostType.BLOG, '📝 Blog'),
            (PostType.NEWS, '📢 News'),
        ]
