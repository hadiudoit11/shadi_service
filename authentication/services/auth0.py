from authlib.integrations.django_client import OAuth
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Initialize OAuth following Auth0 Django quickstart
oauth = OAuth()

try:
    oauth.register(
        name='auth0',
        client_id=settings.AUTH0_CLIENT_ID,
        client_secret=settings.AUTH0_CLIENT_SECRET,
        client_kwargs={
            'scope': settings.AUTH0_SCOPE,
        },
        server_metadata_url=f'https://{settings.AUTH0_DOMAIN}/.well-known/openid-configuration',
        # Auth0 specific configurations
        authorize_params={
            'audience': settings.AUTH0_AUDIENCE,
        } if settings.AUTH0_AUDIENCE else {},
    )
    
    logger.info("Auth0 OAuth client configured successfully")
    
except Exception as e:
    logger.error(f"Failed to configure Auth0 OAuth client: {e}")
    raise