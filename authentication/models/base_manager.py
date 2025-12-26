from django.contrib.auth.models import BaseUserManager


class EventUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')

        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        # Remove reference to EventUser.ADMIN to avoid circular import

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

    def get_or_create_from_auth0(self, auth0_user_data):
        auth0_user_id = auth0_user_data.get('sub')
        email = auth0_user_data.get('email')

        try:
            user = self.get(auth0_user_id=auth0_user_id)
            user.update_from_auth0(auth0_user_data)
            return user, False
        except self.model.DoesNotExist:
            user = self.create_user(
                email=email,
                username=email,
                first_name=auth0_user_data.get('given_name', ''),
                last_name=auth0_user_data.get('family_name', ''),
                auth0_user_id=auth0_user_id,
                auth0_email=email,
                auth0_picture=auth0_user_data.get('picture'),
                auth0_nickname=auth0_user_data.get('nickname'),
            )
            return user, True

