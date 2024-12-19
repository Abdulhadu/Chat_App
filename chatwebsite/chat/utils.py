from .models import ChatMessage, UserStatus, User, Group

def get_unread_counts(user):
    """
    Helper function to get the unread message count for users excluding the current user.
    """
    unread_counts = {}
    online_users = UserStatus.objects.all().exclude(user=user)

    for user_status in online_users:
        unread_count = ChatMessage.objects.filter(
            user=user_status.user, recipient=user, read=False
        ).count()
        unread_counts[user_status.user.username] = unread_count

    return unread_counts, online_users

def get_recipient_from_messages(messages, user):
    """
    Helper function to find the recipient of a chat message.
    """
    for message in messages:
        if message.user != user:
            return message.user
        elif message.recipient != user:
            return message.recipient
    return None

def update_message_timestamps(messages):
    """
    Helper function to update the local timestamps of messages.
    """
    for message in messages:
        message.local_timestamp = message.get_local_timestamp()
