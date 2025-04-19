from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin 
from django.core.validators import FileExtensionValidator
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import models

from .managers import CustomUserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])]
    )
    is_active = models.BooleanField(default=True)
    is_staff  = models.BooleanField(default=False)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()

    def generate_token(self):
        refresh = RefreshToken.for_user(self)
        return {
            "access_token" : str(refresh.access_token),
            "refresh_token" : str(refresh)
        }

    def __str__(self):
        return self.username


