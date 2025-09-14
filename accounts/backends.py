"""
Custom authentication backends for the accounts app.
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in using their email address.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to find user by email or username
            user = User.objects.get(
                Q(email=username) | Q(username=username)
            )
            
            # Check if the password is correct
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            # No user found with the given email/username
            return None
        except User.MultipleObjectsReturned:
            # Multiple users found (shouldn't happen with unique constraints)
            return None
        
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
