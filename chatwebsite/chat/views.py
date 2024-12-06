import datetime
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import ChatMessage

# @login_required
# def chat(request):
#     greeting = "Good Morning" 
#     return render(request, 'chat/lobby.html', {"greeting": greeting, "username": request.user.username})
@login_required
def chat(request):
    greeting = "Good Morning"
    messages = ChatMessage.objects.filter(room="test_name")  # Filter messages by room name
    return render(request, 'chat/lobby.html', {
        "greeting": greeting,
        "username": request.user.username,
        "messages": messages,
    })

def user_signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, "chat/signup.html", {"form": form})

def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Send login event to the WebSocket group
            async_to_sync(get_channel_layer().group_send)(
                "test_group_name",  # Same group name as in the consumer
                {
                    "type": "user_activity",
                    "username": user.username,
                    "activity": "logged in"
                }
            )
            return redirect("chat")
    else:
        form = AuthenticationForm()
    return render(request, "chat/login.html", {"form": form})

def user_logout(request):
    user = request.user
    logout(request)
    async_to_sync(get_channel_layer().group_send)(
        "test_group_name",  
        {
            "type": "user_activity",
            "username": user.username,
            "activity": "logged out"
        }
    )
    return redirect("login")
