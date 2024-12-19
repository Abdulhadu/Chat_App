from django.contrib import admin
from .models import ChatMessage, UserStatus
# Register your models here.
admin.site.register(UserStatus)
admin.site.register(ChatMessage)