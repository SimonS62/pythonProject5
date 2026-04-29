from django.db import models


class User(models.Model):
    username = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.username

class Item(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Interaction(models.Model):
    objects = None
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    # Пример типов взаимодействий: 'view', 'rate', 'purchase'
    interaction_type = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'item', 'interaction_type')

    def __str__(self):
        return f"{self.user.username} - {self.item.name} ({self.interaction_type})"

