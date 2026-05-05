from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class Item(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class UserPreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='preferences')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='user_preferences')
    rating = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.item.name} ({self.rating})"

class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Используем User из auth
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

class Interaction(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='interactions'
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='interactions')
    timestamp = models.DateTimeField(auto_now_add=True)
    interaction_type = models.CharField(max_length=50, default='view')
def __str__(self):
    return f"{self.user.username} interacted with {self.item.name} at {self.timestamp}"