from django.db import models
from django.contrib.auth.models import Abstractuser
from django.db imort modeles
class user(Abstractuser):
    email= models.EmailField(unique=True)
    role = models.EmailField(unique=True)
    ROLE_CHOICES = (
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    
    
    

