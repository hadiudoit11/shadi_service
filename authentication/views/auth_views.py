from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, TemplateView
from django.urls import reverse_lazy, reverse
from django.conf import settings
from django.http import HttpResponseRedirect
from django.contrib import messages
from ..services.auth0 import oauth
from ..models import EventUser
import logging

logger = logging.getLogger(__name__)


class EventUserMixin:
    def get_event_user(self):
        if self.request.user.is_authenticated:
            return self.request.user
        return None
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event_user'] = self.get_event_user()
        return context


class Auth0LoginRequiredMixin(LoginRequiredMixin):
    login_url = reverse_lazy('auth:login')
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse('auth:login'))
        
        # Verify Auth0 authentication
        if not request.user.auth0_user_id:
            logger.warning(f"User {request.user.email} lacks Auth0 ID, forcing re-authentication")
            logout(request)
            messages.warning(request, 'Please log in with Auth0.')
            return HttpResponseRedirect(reverse('auth:login'))
        
        # Verify session integrity (Auth0 session should match Django user)
        session_auth0_id = request.session.get('auth0_user_id')
        if session_auth0_id and session_auth0_id != request.user.auth0_user_id:
            logger.warning(f"Session Auth0 ID mismatch for user {request.user.email}")
            logout(request)
            messages.warning(request, 'Session expired. Please log in again.')
            return HttpResponseRedirect(reverse('auth:login'))
        
        return super().dispatch(request, *args, **kwargs)


class LoginView(View):
    def get(self, request):
        # Store next URL in session for post-login redirect
        next_url = request.GET.get('next')
        if next_url:
            request.session['next_url'] = next_url
        
        redirect_uri = request.build_absolute_uri(reverse('auth:callback'))
        
        # Auth0 recommended approach with proper error handling
        try:
            return oauth.auth0.authorize_redirect(
                request, 
                redirect_uri,
                # Optional: Add additional parameters
                prompt='login'  # Force user to re-authenticate
            )
        except Exception as e:
            logger.error(f"Auth0 login redirect failed: {e}")
            messages.error(request, 'Login service temporarily unavailable. Please try again.')
            return redirect('/')


class CallbackView(View):
    def get(self, request):
        try:
            # Get access token from Auth0 following their recommended flow
            token = oauth.auth0.authorize_access_token(request)
            
            # Validate token exists and has userinfo
            if not token:
                logger.warning("No token received from Auth0")
                messages.error(request, 'Authentication failed. No token received.')
                return redirect('auth:login')
            
            user_info = token.get('userinfo')
            if not user_info:
                logger.warning("No userinfo in token from Auth0")
                messages.error(request, 'Failed to get user information from Auth0.')
                return redirect('auth:login')
            
            # Validate required user info fields
            required_fields = ['sub', 'email']
            missing_fields = [field for field in required_fields if not user_info.get(field)]
            if missing_fields:
                logger.error(f"Missing required user info fields: {missing_fields}")
                messages.error(request, 'Incomplete user information received.')
                return redirect('auth:login')
            
            # Create or get user following Auth0 best practices
            user, created = EventUser.objects.get_or_create_from_auth0(user_info)
            
            # Log user in with specific backend
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            # Store Auth0 session info for future reference
            request.session['auth0_user_id'] = user_info.get('sub')
            request.session['auth0_access_token'] = token.get('access_token')
            
            # Show appropriate welcome message
            if created:
                messages.success(request, f'Welcome {user.display_name}! Your account has been created.')
                logger.info(f"New user created from Auth0: {user.email}")
            else:
                messages.success(request, f'Welcome back {user.display_name}!')
                logger.info(f"User logged in via Auth0: {user.email}")
            
            # Redirect to frontend with auth token/session info
            next_url = request.session.get('next_url', settings.LOGIN_REDIRECT_URL)
            if 'next_url' in request.session:
                del request.session['next_url']
            
            # Add success parameter to let frontend know auth was successful
            redirect_url = f"{next_url}?auth=success&user_id={user.id}"
            
            return redirect(redirect_url)
            
        except Exception as e:
            logger.error(f"Auth0 callback error: {str(e)}", exc_info=True)
            messages.error(request, 'Authentication failed. Please try again.')
            return redirect('auth:login')


class LogoutView(View):
    def get(self, request):
        # Log the logout attempt
        if request.user.is_authenticated:
            logger.info(f"User logging out: {request.user.email}")
        
        # Clear Django session first
        logout(request)
        
        # Clear Auth0-specific session data
        if 'auth0_user_id' in request.session:
            del request.session['auth0_user_id']
        if 'auth0_access_token' in request.session:
            del request.session['auth0_access_token']
        
        # Construct Auth0 logout URL following their recommendations
        return_to = request.build_absolute_uri(settings.LOGOUT_REDIRECT_URL)
        logout_url = (
            f"https://{settings.AUTH0_DOMAIN}/v2/logout"
            f"?client_id={settings.AUTH0_CLIENT_ID}"
            f"&returnTo={return_to}"
        )
        
        return HttpResponseRedirect(logout_url)


class ProfileView(Auth0LoginRequiredMixin, EventUserMixin, TemplateView):
    template_name = 'auth/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'My Profile'
        return context


class DashboardView(Auth0LoginRequiredMixin, EventUserMixin, TemplateView):
    template_name = 'auth/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dashboard'
        return context