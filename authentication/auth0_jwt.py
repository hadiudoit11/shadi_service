import jwt
import json
import requests
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework import authentication, exceptions
from rest_framework.authentication import BaseAuthentication
from django.core.cache import cache


User = get_user_model()


class Auth0JSONWebTokenAuthentication(BaseAuthentication):
    """
    Auth0 JWT token authentication for DRF API endpoints
    Validates JWT tokens from Auth0 and gets/creates Django users
    """
    
    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header:
            return None
            
        try:
            # Extract token from "Bearer <token>" format
            auth_type, token = auth_header.split(' ', 1)
            if auth_type.lower() != 'bearer':
                return None
        except ValueError:
            return None
            
        try:
            # Validate and decode the JWT token
            payload = self.decode_jwt(token)
            user = self.get_or_create_user(payload)
            return (user, token)
            
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token')
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Authentication failed: {str(e)}')
    
    def decode_jwt(self, token):
        """
        Decode and validate JWT token from Auth0
        """
        # Get Auth0 domain from settings
        auth0_domain = getattr(settings, 'AUTH0_DOMAIN', '')
        if not auth0_domain:
            raise exceptions.AuthenticationFailed('AUTH0_DOMAIN not configured')
            
        # Get the signing key from Auth0's JWKS endpoint
        signing_key = self.get_signing_key(token, auth0_domain)
        
        # Decode and validate the token
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=['RS256'],
            audience=getattr(settings, 'AUTH0_CLIENT_ID', ''),
            issuer=f'https://{auth0_domain}/'
        )
        
        return payload
    
    def get_signing_key(self, token, auth0_domain):
        """
        Get the signing key from Auth0's JWKS endpoint
        """
        # Cache key for JWKS data
        cache_key = f'auth0_jwks_{auth0_domain}'
        jwks = cache.get(cache_key)
        
        if not jwks:
            # Fetch JWKS from Auth0
            jwks_url = f'https://{auth0_domain}/.well-known/jwks.json'
            response = requests.get(jwks_url, timeout=10)
            response.raise_for_status()
            jwks = response.json()
            
            # Cache for 1 hour
            cache.set(cache_key, jwks, 3600)
        
        # Get the key ID from token header
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get('kid')
        
        if not kid:
            raise exceptions.AuthenticationFailed('Token missing key ID')
            
        # Find the matching key in JWKS
        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                # Convert JWK to PEM format for PyJWT
                from cryptography.hazmat.primitives.asymmetric import rsa
                from cryptography.hazmat.primitives import serialization
                import base64
                
                # Extract RSA key components
                n = base64.urlsafe_b64decode(self._pad_base64(key['n']))
                e = base64.urlsafe_b64decode(self._pad_base64(key['e']))
                
                # Create RSA public key
                public_numbers = rsa.RSAPublicNumbers(
                    int.from_bytes(e, 'big'),
                    int.from_bytes(n, 'big')
                )
                public_key = public_numbers.public_key()
                
                # Convert to PEM format
                pem_key = public_key.serialize(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                
                return pem_key
                
        raise exceptions.AuthenticationFailed('Unable to find matching key')
    
    def _pad_base64(self, s):
        """Add padding to base64 string if needed"""
        return s + '=' * (4 - len(s) % 4)
    
    def get_or_create_user(self, payload):
        """
        Get or create Django user based on Auth0 JWT payload
        """
        # Extract user info from JWT payload
        auth0_user_id = payload.get('sub')  # Auth0 user ID
        email = payload.get('email')
        
        if not auth0_user_id:
            raise exceptions.AuthenticationFailed('Token missing user ID')
            
        try:
            # Try to find existing user by Auth0 ID
            user = User.objects.get(auth0_user_id=auth0_user_id)
        except User.DoesNotExist:
            # Try to find by email if available
            if email:
                try:
                    user = User.objects.get(email=email)
                    # Link Auth0 ID to existing user
                    user.auth0_user_id = auth0_user_id
                    user.save()
                except User.DoesNotExist:
                    # Create new user
                    user = self.create_user_from_auth0(payload)
            else:
                raise exceptions.AuthenticationFailed('Cannot create user without email')
        
        # Update user data from Auth0 token
        self.update_user_from_token(user, payload)
        
        return user
    
    def create_user_from_auth0(self, payload):
        """
        Create a new Django user from Auth0 JWT payload
        """
        auth0_user_id = payload.get('sub')
        email = payload.get('email')
        
        # Extract name information
        name = payload.get('name', '')
        given_name = payload.get('given_name', '')
        family_name = payload.get('family_name', '')
        
        # Use given/family names if available, otherwise split name
        if given_name and family_name:
            first_name = given_name
            last_name = family_name
        elif name:
            name_parts = name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
        else:
            first_name = email.split('@')[0] if email else 'User'
            last_name = ''
        
        user = User.objects.create_user(
            username=email or auth0_user_id,  # Use email as username
            email=email,
            first_name=first_name,
            last_name=last_name,
            auth0_user_id=auth0_user_id
        )
        
        return user
    
    def update_user_from_token(self, user, payload):
        """
        Update user information from Auth0 JWT payload
        """
        # Update Auth0-specific fields
        user.auth0_roles = payload.get('https://shadi.com/roles', [])
        user.auth0_permissions = payload.get('https://shadi.com/permissions', [])
        
        # Update picture if available
        picture = payload.get('picture')
        if picture:
            user.auth0_picture = picture
        
        # Update email verified status
        email_verified = payload.get('email_verified', False)
        if email_verified and not user.is_active:
            user.is_active = True
        
        # Save changes
        user.save()
    
    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response.
        """
        return 'Bearer realm="api"'