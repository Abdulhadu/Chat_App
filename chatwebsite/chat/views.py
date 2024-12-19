
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import ChatMessage, User, Group
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .utils import get_recipient_from_messages, get_unread_counts, update_message_timestamps

# Personal chat retrieval
@login_required
def home(request):
    greeting = "Good Morning"
    unread_counts, online_users = get_unread_counts(request.user)

    all_users = User.objects.exclude(username=request.user.username)
    user_groups = Group.objects.filter(members=request.user)

    return render(request, "chat/room.html", {
        "greeting": greeting,
        "username": request.user.username,
        "online_users": online_users,
        "unread_counts": unread_counts,
        "all_users": all_users,
        "user_groups": user_groups
    })

# Personal chat retrieval
@login_required
def room(request, room_name):
    greeting = "Good Morning"
    unread_counts, online_users = get_unread_counts(request.user)

    all_users = User.objects.exclude(username=request.user.username)
    user_groups = Group.objects.filter(members=request.user)

    room_group_name = f"chat_{'_'.join(sorted([request.user.username, room_name]))}"
    messages = ChatMessage.objects.filter(room=room_group_name).order_by('timestamp')
    update_message_timestamps(messages)
    recipient = get_recipient_from_messages(messages, request.user)
   
    return render(request, "chat/room.html", {
        "greeting": greeting,
        "username": request.user.username,
        "online_users": online_users,
        "messages": messages,
        "room_name": room_name,
        "recipient": recipient.username if recipient else None,
        "unread_counts": unread_counts,
        "all_users": all_users,
        "user_groups": user_groups
    })

# Group chat retrieval
@login_required
def group(request, group_name):
    greeting = "Good Morning"
    unread_counts, online_users = get_unread_counts(request.user)

    all_users = User.objects.exclude(username=request.user.username)
    user_groups = Group.objects.filter(members=request.user)

    group = get_object_or_404(Group, name=group_name)
    messages = group.messages.all().order_by('timestamp')
    room_name = group_name
    update_message_timestamps(messages)
    recipient = get_recipient_from_messages(messages, request.user)

    return render(request, "chat/room.html", {
        "greeting": greeting,
        "username": request.user.username,
        "online_users": online_users,
        "messages": messages,
        "room_name": room_name,
        "recipient": recipient.username if recipient else None,
        "unread_counts": unread_counts,
        "all_users": all_users,
        "user_groups": user_groups
    })


# Create group chat
@csrf_exempt
@login_required
@require_POST
def create_group(request):
    group_name = request.POST.get('group_name')
    selected_users = request.POST.getlist('selected_users')

    if not group_name:
        return JsonResponse({'success': False, 'error': 'Group name is required'})

    if Group.objects.filter(name=group_name).exists():
        return JsonResponse({'success': False, 'error': 'Group name already exists'})

    try:
        group = Group.objects.create(name=group_name, creator=request.user)
        selected_user_objects = User.objects.filter(username__in=selected_users)
        group.members.add(request.user)
        group.members.add(*selected_user_objects)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "broadcast",
            {
                "type": "group_notification",
                "group_name": group_name,
                "creator": request.user.username,
                "members": list(selected_users)
            }
        )

        return JsonResponse({
            'success': True, 
            'group_name': group_name, 
            'members': list(selected_users)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    

# User signup
def user_signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, "chat/signup.html", {"form": form})


# User login
def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            async_to_sync(get_channel_layer().group_send)(
                f"chat_{user.username}", 
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


# User logout
def user_logout(request):
    user = request.user
    logout(request)
    async_to_sync(get_channel_layer().group_send)(
        f"chat_{user.username}",
        {
            "type": "user_activity",
            "username": user.username,
            "activity": "logged out"
        }
    )
    return redirect("login")