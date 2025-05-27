import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from django.utils import timezone

from .models import *
from users.models import *
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist



# -------------------- Chat --------------
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.request_user = self.scope['user']
            if self.request_user.is_authenticated:
                # Get the ID of the user the current user is chatting with (from the URL)
                self.chat_with_user = self.scope["url_route"]["kwargs"]["id"]
                
                user_ids = [int(self.request_user.id), int(self.chat_with_user)]
                user_ids = sorted(user_ids)
                self.room_group_name = f"chat_{user_ids[0]}-{user_ids[1]}"

                await self.channel_layer.group_add(self.room_group_name, self.channel_name)
                self.chat_room = await self.get_or_create_chat_room()
                
                # set user to active user
                await self.add_user_to_active_chat(self.chat_room[0].id, self.request_user.id)

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
                    "username": result['username'],
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
        
        chat_room.last_message_timestamp = message.timestamp
        chat_room.save(update_fields=["last_message_timestamp"])
        
        return {
            'message_id': message.id,
            'timestamp': message.timestamp.isoformat(),  
            'username': message.user.username,
            'seen': message.seen,
        }
    



    async def disconnect(self, code):
        try:
            
            # remove user from active chat user list
            if hasattr(self, 'chat_room') and self.chat_room:
                await self.remove_user_from_active_chat(self.chat_room[0].id, self.request_user.id)
                
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
        except Exception as e:
            print(f"Error in disconnect: {str(e)}")




    async def chat_message(self, event):

        recipient_user_id = int(self.chat_with_user)

        is_recipient_active = await self.is_user_active_in_chat(self.chat_room[0].id, recipient_user_id)
        unread_message_count = 0
        message_seen = event['seen']

        if is_recipient_active:
            message_seen = True
            await self.mark_messages_as_marked(event['message_id'])
        else:
            unread_message_count = await self.get_unread_messages_count(self.chat_room[0].id, recipient_user_id)


              
       

        await self.send(text_data=json.dumps({
            "type": "message",
            "chat_room_id": self.chat_room[0].id,
            "message_id": event['message_id'],
            "content": event['content'],
            "user": event['user'],  
            "receiver_id": recipient_user_id,
            "timestamp": event['timestamp'],
            "seen": message_seen,
        }))

        await self.channel_layer.group_send(
            f"user_status_{recipient_user_id}",
            {
                "type": "unread_count_update",
                "chat_room_id": self.chat_room[0].id,
                "sender_id": event['user'],
                "username": event['username'],
                "unread_count": unread_message_count,
                "last_message": event['content'],
                "timestamp": event['timestamp']
            }
        )

    
    # adding users to active chat
    @database_sync_to_async
    def add_user_to_active_chat(self, chat_room_id, user_id):
        active_chats = cache.get(f'active_chats_{chat_room_id}', {})
        active_chats[user_id] = True
        cache.set(f'active_chats_{chat_room_id}', active_chats, timeout=None)

    
    # remove users from active chat
    @database_sync_to_async
    def remove_user_from_active_chat(self, chat_room_id, user_id):
        active_chats = cache.get(f'active_chats_{chat_room_id}', {})
        if user_id in active_chats:
            del active_chats[user_id]
            cache.set(f'active_chats_{chat_room_id}', active_chats, timeout=None)


    # check user is active or not
    @database_sync_to_async
    def is_user_active_in_chat(self, chat_room_id, user_id):
        active_chats = cache.get(f'active_chats_{chat_room_id}', {})
        return active_chats.get(user_id, False)


    # get unread messages count
    @database_sync_to_async
    def get_unread_messages_count(self, chat_room_id, recipient_user_id):
        return Messages.objects.filter(
            chat_room_id=chat_room_id,
            seen=False
        ).exclude(user_id=recipient_user_id).count()
    

    # Mark messages as read
    @database_sync_to_async
    def mark_messages_as_marked(self, message_id):
        Messages.objects.filter(id=message_id).update(seen=True)




# ----------------------   Notification -------------------


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f'notifications_{self.user_id}'
        self.status_group_name = f'user_status_{self.user_id}'


        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.channel_layer.group_add(
            self.status_group_name,
            self.channel_name
        )

        await self.channel_layer.group_add(
            "global_online_users",
            self.channel_name
        )
        

        # Mark user as online
        await self.set_user_online(self.user_id)

        # Update online users list
        await self.broadcast_online_users()



        await self.accept()


    async def disconnect(self, close_code):
        try:
            # Remove user from online users 
            await self.set_user_offline(self.user_id)

            # Brodcast updated online user list
            await self.broadcast_online_users()

            await self.channel_layer.group_discard(
                self.status_group_name,
                self.channel_name
            )

            await self.channel_layer.group_discard(
                "global_online_users",
                self.channel_name
            )

            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            
            
        except Exception as e:
            print(f"Error in status disconnect: {str(e)}")



    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        if action == "chat_message":
            # message = data['message']
            message = data.get("message")
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'notification_message',
                    'message': message
                }
            )

        elif action == "mark_as_read":
            chat_room_id = data.get('chat_room_id')
            recipient_user_id = data.get('recipient_id')
            message_data = await self.mark_messages_as_read(chat_room_id)

            await self.channel_layer.group_send(
                f"user_status_{self.user_id}",
                {
                    "type": "unread_count_update",
                    "chat_room_id": chat_room_id,
                    "sender_id": recipient_user_id,
                    "username": "mark_as_read",
                    "unread_count": message_data['unread_count'],
                    "last_message": message_data['last_message_content'],
                    "timestamp": message_data['last_message_timestamp'],
                }
            )
            

    async def notification_message(self, event):
        message = event['message']

        await self.send(text_data=json.dumps({
            'message': message
        }))


    @database_sync_to_async
    def mark_messages_as_read(self, chat_room_id):
        # Mark all unread messages in this chat room as read
        Messages.objects.filter(
            chat_room_id=chat_room_id,
            seen=False
        ).exclude(user=self.user_id).update(seen=True)

        unread_count = Messages.objects.filter(
            chat_room_id=chat_room_id,
            seen=False
        ).exclude(user=self.user_id).count()

        last_message = Messages.objects.filter(chat_room_id=chat_room_id).order_by('-timestamp').first()
        last_message_content = last_message.content if last_message else None
        last_message_timestamp = last_message.timestamp.isoformat() if last_message else None
        

        return {
            "unread_count": unread_count,
            "last_message_content": last_message_content,
            "last_message_timestamp": last_message_timestamp
        }


    
    async def user_status(self, event):
        await self.send(text_data=json.dumps({
            "type": "user_status",
            "user_id": event['user_id'],
            "online": event['online'],
            "last_seen": event['last_seen'],

        }))
    

    async def unread_count_update(self, event):
        # Send unread count updates to the recipient side
        await self.send(text_data=json.dumps({
            "type": "unread_update",
            "chat_room_id": event["chat_room_id"],
            "sender_id": event["sender_id"],
            "username": event["username"],
            "unread_count": event["unread_count"],
            "last_message": event.get("last_message"),
            "timestamp": event.get("timestamp")

        }))

    # Mark user to online users
    async def set_user_online(self, user_id):
        online_users = cache.get("online_users", {})
        online_users[user_id] = True
        cache.set("online_users", online_users, timeout=None) 


    # Remove user from online users list     
    async def set_user_offline(self, user_id):
        online_users = cache.get("online_users", {})
        if user_id in online_users:
            del online_users[user_id]
            cache.set("online_users", online_users, timeout=None)


    async def broadcast_online_users(self):
        online_users = cache.get("online_users", {})
        await self.channel_layer.group_send(
            "global_online_users",
            {
                "type":"send_online_users",
                "online_users": list(online_users.keys())
            }
        )
    

    # Handle online users update event
    async def send_online_users(self, event):
        await self.send(text_data=json.dumps({
            "type":"online_users",
            "online_users":event["online_users"]
        }))

