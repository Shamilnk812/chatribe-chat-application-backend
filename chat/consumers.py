import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from django.utils import timezone

from .models import *
from users.models import *
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist



class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.request_user = self.scope['user']
            if self.request_user.is_authenticated:
                self.chat_with_user = self.scope["url_route"]["kwargs"]["id"]
                user_ids = [int(self.request_user.id), int(self.chat_with_user)]
                user_ids = sorted(user_ids)
                self.room_group_name = f"chat_{user_ids[0]}-{user_ids[1]}"

                await self.channel_layer.group_add(self.room_group_name, self.channel_name)
                self.chat_room = await self.get_or_create_chat_room()
                
                await self.accept()
            else:
                await self.close()
        except Exception as e:
            print(f"Error in connect: {str(e)}")
            await self.close()



    @database_sync_to_async
    def get_or_create_chat_room(self):
        user1 = self.request_user
        user2 = User.objects.get(id=self.chat_with_user)
        user_ids = sorted([user1.id, user2.id])

        chat_room, created = ChatRooms.objects.get_or_create(
            user1_id=user_ids[0],
            user2_id=user_ids[1],
            defaults={'user1_id': user_ids[0], 'user2_id': user_ids[1]}
        )
        return chat_room, created
    


    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data.get("message")
            result = await self.save_message(message)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message_id": result['message_id'],
                    "content": message,
                    "user": self.request_user.id, 
                    "timestamp": result['timestamp'],  
                    "seen": result['seen'],
                }
            )


        except Exception as e:
            await self.send(text_data=json.dumps({"error": str(e)}))
    
     
    @database_sync_to_async
    def save_message(self, message_content):
        chat_room = self.chat_room[0]
        message = Messages.objects.create(
            chat_room=chat_room,
            user=self.request_user,
            content=message_content,
            seen=False
        )
     
        return {
            'message_id': message.id,
            'timestamp': message.timestamp.isoformat(),  
            'seen': message.seen ,
        }
    



    async def disconnect(self, code):
        try:
            
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
        except Exception as e:
            print(f"Error in disconnect: {str(e)}")




    async def chat_message(self, event):
       

        await self.send(text_data=json.dumps({
            "type": "message",
            "message_id": event['message_id'],
            "content": event['content'],
            "user": event['user'],  
            "timestamp": event['timestamp'],
        }))


       



# ----------------------   Notification -------------------


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f'notifications_{self.user_id}'


        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']


        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'notification_message',
                'message': message
            }
        )
        

    async def notification_message(self, event):
        message = event['message']

        await self.send(text_data=json.dumps({
            'message': message
        }))


