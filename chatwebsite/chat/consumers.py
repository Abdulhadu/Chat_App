import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        if self.scope["user"].is_authenticated:
            self.user = self.scope["user"]
            print("user is ", self.user)
        else:
            self.close()  
            return
        self.room_name = self.scope["url_route"]["kwargs"].get("room_name")
        from .models import Group
        
        try:
            Group.objects.get(name=self.room_name)
            self.room_group_name = f"group_{self.room_name}"
        except Group.DoesNotExist:
            self.room_group_name = f"chat_{'_'.join(sorted([self.user.username, self.room_name]))}"
        
        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )
        
        from .models import UserStatus
        UserStatus.objects.update_or_create(user=self.user, defaults={'is_online': True})

        self.accept()
        self.send(text_data=json.dumps({"status": "Connected from django channels", "message": "you are now connected", "room_group_name": self.room_group_name})) 

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    def receive(self, text_data, bytes_data=None):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', '')
          
            if message_type == 'mark_seen':
                message_id = text_data_json.get('message_ids') 
                self.mark_messages(message_id)
                         
                         
            elif message_type == "chat":
                message = text_data_json.get("message", "")
                # print("message is " , message)
                recipient_username = text_data_json.get("recipient", "")
                room_name = text_data_json.get("room_name", "")
                # print("room name is" , room_name)
                # print("recipent is" , recipient_username)
               
                from .models import ChatMessage, User, Group
                try:
                    group = Group.objects.get(name=room_name)
                    # print("group name is" , group)
                    room_group_name = self.room_name
                    # print("room group name is" , room_group_name)
                    chat_message = ChatMessage.objects.create(
                        user=self.user,
                        group=group,
                        message=message,
                        room=f"group_{group.name}",
                        status="sending",
                        read=False
                    )
                    async_to_sync(self.channel_layer.group_send)(
                        f"group_{group.name}",
                        {
                            "type": "chat_message",
                            "message_id": chat_message.id,
                            "message": message,
                            "username": self.user.username,
                            "status": "sending"
                        }
                    )
               
                except Group.DoesNotExist:
                    room_group_name = self.room_group_name
                    # print("room group name is" , room_group_name)
                    recipient_user = User.objects.get(username=recipient_username)
                    chat_message = ChatMessage.objects.create(
                        user=self.user,
                        recipient=recipient_user,
                        message=message,
                        room=room_group_name,
                        status="sending",
                        read=False
                    )
                    async_to_sync(self.channel_layer.group_send)(
                        self.room_group_name,
                        {
                            "type": "chat_message",
                            "message_id": chat_message.id,
                            "message": message,
                            "username": self.user.username,
                            "status": "sending"
                        }
                    )
                    
        except Exception as e:
            print("error in saving", e)
            
    
    def mark_messages(self, message_ids):
        from .models import ChatMessage
    
        try:
            messages_to_mark = ChatMessage.objects.filter(
                id__in=message_ids,
                recipient=self.user  
            )

            messages_to_mark.update(
                
                status="seen", 
                read=True
            )
    
            # Prepare unread counts
            unread_counts = {}
            from .models import UserStatus
            online_users = UserStatus.objects.all().exclude(user=self.user)    
            
            for user_status in online_users:
                unread_count = ChatMessage.objects.filter(
                    user=user_status.user, 
                    recipient=self.user, 
                    read=False
                ).count()
                unread_counts[user_status.user.username] = unread_count
    
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'status_update',
                    'message_ids': list(messages_to_mark.values_list('id', flat=True)),
                    "unread_counts": unread_counts,
                    'user_id': self.user.id
                }
            )
        except Exception as e:
            print("Error in mark_messages_as_seen: ", e)



    def chat_message(self, event):
        message_id = event.get("message_id")
        message = event["message"]
        username = event["username"]
        status = event.get("status", "sending")
        
        if status == "sending":
            from .models import ChatMessage
            ChatMessage.objects.filter(id=message_id).update(status="delivered")
        
        self.send(text_data=json.dumps({
            "type": "chat",
            "message_id": message_id,
            "message": message,
            "username": username,
            "status": "delivered"
        }))
        
        
        
    def user_activity(self, event):
        username = event["username"]
        activity = event["activity"]
        self.send(text_data=json.dumps({
            "type": "user_activity",
            "username": username,
            "activity": activity
        }))
        
        
    def status_update(self, event):
        self.send(text_data=json.dumps({
            "type": "status_update",
            "message_ids": event.get("message_ids"),
            "unread_counts": event.get("unread_counts"),
            "user_id": event.get("user_id")
        }))
        
 