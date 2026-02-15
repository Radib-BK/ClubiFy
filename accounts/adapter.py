from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_username
from django.contrib.auth import get_user_model


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter to generate unique usernames for social account signups.
    Uses firstname_lastname format instead of just first name.
    """

    def populate_user(self, request, sociallogin, data):
        """
        Override to customize username generation for social logins.
        """
        user = super().populate_user(request, sociallogin, data)

        # Get first and last name from Google data
        first_name = data.get("first_name", "") or ""
        last_name = data.get("last_name", "") or ""

        # Clean names (keep only alphanumeric characters)
        first_name = "".join(c for c in first_name if c.isalnum()).lower()
        last_name = "".join(c for c in last_name if c.isalnum()).lower()

        # Build username as firstname_lastname
        if first_name and last_name:
            base_username = f"{first_name}_{last_name}"
        elif first_name:
            base_username = first_name
        elif last_name:
            base_username = last_name
        else:
            # Fallback to email prefix if no name available
            email = data.get("email", "")
            base_username = email.split("@")[0] if email else "user"
            base_username = "".join(
                c for c in base_username if c.isalnum() or c == "_"
            ).lower()

        # Make sure username is unique
        username = self._generate_unique_username(base_username)
        user_username(user, username)

        return user

    def _generate_unique_username(self, base_username):
        """
        Generate a unique username by appending a number if needed.
        """
        User = get_user_model()

        # First try the base username as-is
        if not User.objects.filter(username=base_username).exists():
            return base_username

        # If taken, append incrementing number
        counter = 1
        while True:
            candidate = f"{base_username}{counter}"
            if not User.objects.filter(username=candidate).exists():
                return candidate
            counter += 1
