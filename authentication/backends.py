from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    """
    Custom authentication backend that allows login with either email or username.
    This is useful for Django admin where users might expect to use their email.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        
        if username is None or password is None:
            return None
        
        # Try to find user by email first, then by username
        user = None
        
        # Try email authentication
        try:
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            pass
        
        # If not found by email, try username
        if user is None:
            try:
                user = User.objects.get(username__iexact=username)
            except User.DoesNotExist:
                return None
        
        # Check password
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None