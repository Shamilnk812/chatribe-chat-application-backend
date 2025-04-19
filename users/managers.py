from django.contrib.auth.models import BaseUserManager


class CustomUserManager(BaseUserManager):
    
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError("User must have an email address")
        user = self.model(
            email=self.normalize_email(email),
            username=username,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    


    def create_superuser(self, email, username, password):
        user = self.create_user(
            email=email,
            username=username,
            password=password
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
    

