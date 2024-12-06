from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages")
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    room = models.CharField(max_length=255)  
    status = models.CharField(
        max_length=10, 
        choices=[('sending', 'Sending'), ('delivered', 'Delivered'), ('seen', 'Seen')], 
        default='sending'
    )
    
    def __str__(self):
        return f"{self.user.username}: {self.message} ({self.timestamp})"