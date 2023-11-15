from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _

# Create your models here.

class CustomUserManager(BaseUserManager):
    
    def create_user(self, username, password, email, first_name, last_name, **otherfields):
        if not email:
            raise ValueError(_('You must provide an email address'))
        if not first_name:
            raise ValueError(_('You must provide your first name'))
        if not last_name:
            raise ValueError(_('You must provide your last name'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, first_name=first_name, last_name=last_name, **otherfields)
        user.set_password(password)
        user.save()
        return user
    
    def create_superuser(self, username, password, email, first_name, last_name, **otherfields):
        otherfields.setdefault('is_staff', True)
        otherfields.setdefault('is_superuser', True)
        otherfields.setdefault('is_active', True)
        otherfields.setdefault('status', 'admin')
        
        if otherfields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True'))
        if otherfields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True'))
        
        return self.create_user(username, password, email, first_name, last_name, **otherfields)
            

class CustomUser(AbstractBaseUser, PermissionsMixin):
    
    username = models.CharField(max_length=150, unique=True)
    USERNAME_FIELD = "username"
    
    email = models.EmailField(_("email address"))
    EMAIL_FIELD = "email"
    
    STATUS = (
        ('student', 'student'),
        ('teacher','teacher'),
        ('admin', 'admin'),
    )
    status = models.CharField(max_length=100, choices=STATUS, default='student')
    
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    description = models.TextField('Description', max_length=600, default='', blank=True)
    
    profile_picture = models.ImageField(upload_to='users/images', null=True, blank=True)
    
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    
    objects = CustomUserManager()
    
    def __str__(self):
        return self.username
    

