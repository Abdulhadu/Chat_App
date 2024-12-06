import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import html
from django.utils.html import escape
# async_to_sync(channel_layer.send)("channel_name", {...})
# from .models import ChatMessage
# from .models import ChatMessage

class TestConsumer(WebsocketConsumer):
    # groups = ["broadcast"]

    def connect(self):
        if self.scope["user"].is_authenticated:
            self.user = self.scope["user"]
            print("user is ", self.user)
        else:
            self.close()  # Reject connection if the user is not authenticated
            return
        self.room_name = "test_name" #specify the room name 
        self.room_group_name = "test_group_name" # specify the group name
        async_to_sync(self.channel_layer.group_add)( # code to add the user in groups 
             self.room_group_name, self.channel_name
        )
        # channel name are automatically taken as the name of user because each user contain separate channels 
        self.accept()
        self.send(text_data=json.dumps({"status": "Connected from django channels", "message": "you are now connected"}))

    def receive(self, text_data=None, bytes_data=None):
        try:
            text_data_json = json.loads(text_data)
            try:
                message_type = text_data_json.get('type', '')
                print("message type is ", message_type)
                if message_type == "mark_seen":
                    message_ids = text_data_json.get("message_ids", [])
                    if message_ids:
                         self.mark_seen(message_ids)
                         

                elif message_type == "chat":
                    from .models import ChatMessage
                    message = text_data_json.get("message", "")
                    username = text_data_json.get("username", "")
        
                    chat_message = ChatMessage.objects.create(
                        user=self.user,
                        room=self.room_name,
                        message=message,
                        status="sending"
                    )
                    
                    async_to_sync(self.channel_layer.group_send)(
                        self.room_group_name,
                        {
                            "type": "chat_message",
                            "message_id": chat_message.id,
                            "message": message,
                            "username": username,
                            "status": "sending"
                        }
                    )   
                    
            except Exception as e:
                print("error in saving", e)
      
        except json.JSONDecodeError:
            self.send(text_data=json.dumps({"error": "Invalid JSON format"}))
        
     

    def disconnect(self, *args, **kargs):
        print("User disconnected:", self.user)
        # Handle logout notification
        # async_to_sync(self.channel_layer.group_send)(
        #     self.room_group_name,
        #     {
        #         "type": "user_activity",
        #         "username": self.user.username,
        #         "activity": "logged out"
        #     }
        # )

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
        # Send login/logout alert to all users
        self.send(text_data=json.dumps({
            "type": "user_activity",
            "username": username,
            "activity": activity
        }))
        
        
    def mark_seen(self, message_ids):
        from .models import ChatMessage
        try:
            print("under mark seen function")
            ChatMessage.objects.filter(id__in=message_ids).update(status="seen")
            self.send(text_data=json.dumps({
                "type": "status_update",
                "message_ids": message_ids,
                "status": "seen"
            }))
        except Exception as e:
            print("Error in mark_seen: ", e)
    
    # def send_notification(self, event):
    #     print("send notifications")
    #     print(event.get('value'))
    #     value = event.get('value')
    #     self.send(text_data=json.dumps({"status": "Notification recieved", "Payload": value }))
    #     print("send notifications")
      
    # def chat_message(self, event):
    #     # Send message to WebSocket
    #     message = event["message"]
    #     username = event['username']
    #     self.send(text_data=json.dumps(    {
    #                 "type": "chat",
    #                 "message":  message,
    #                 "username": username
    #             }))