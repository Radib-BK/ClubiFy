from django import template

register = template.Library()


@register.filter
def profile_picture(user):
    """
    Returns the user's profile picture URL if they signed in with Google,
    otherwise returns None.

    Usage: {{ user|profile_picture }}
    """
    if not user or not user.is_authenticated:
        return None

    try:
        # Check if user has a social account (Google)
        social_accounts = user.socialaccount_set.all()
        for account in social_accounts:
            if account.provider == "google":
                # Get the picture URL from extra_data
                picture = account.extra_data.get("picture")
                if picture:
                    return picture
    except Exception:
        pass

    return None


@register.simple_tag
def get_profile_picture(user):
    """
    Returns the user's profile picture URL if they signed in with Google,
    otherwise returns None.

    Usage: {% get_profile_picture user as profile_pic %}
    """
    return profile_picture(user)
