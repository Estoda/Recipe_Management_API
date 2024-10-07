from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.conf import settings

class User(AbstractUser):
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)

class Recipe(models.Model):
    CATEGORY_CHOICES = [
        ('Dessert', 'Dessert'),
        ('Main Course', 'Main Course'),
        ('Appetizer', 'Appetizer'),
        ('Beverage', 'Beverage'),
    ]

    title = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    ingredients = models.JSONField()
    instructions = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    preparation_time = models.PositiveIntegerField(help_text='Time in minutes')
    cooking_time = models.PositiveIntegerField(help_text='Time in minutes')
    servings = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipes')

    def __str__(self):
        return self.title

