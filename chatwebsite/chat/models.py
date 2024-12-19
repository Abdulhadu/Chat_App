from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import localtime

class Group(models.Model):
    name = models.CharField(max_length=100, unique=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(User,related_name='chat_groups')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    room = models.CharField(max_length=25)
    read = models.BooleanField(default=False) 
    status = models.CharField(
        max_length=10,
        choices=[('sending', 'Sending'), ('delivered', 'Delivered'), ('seen', 'Seen')],
        default='sending'
    )
    def get_local_timestamp(self):
        """Returns the timestamp in local time (PKT)."""
        return localtime(self.timestamp)
    
            
class UserStatus(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_online = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} is {'online' if self.is_online else 'offline'}"
    
    
