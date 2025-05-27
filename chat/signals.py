from django.db.models.signals import post_save,pre_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.cache import cache
from .models import *



# Utility Function for Real-Time Notifications


def send_real_time_notification(user_id,message) :
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'notifications_{user_id}',
        {
            'type':'notification_message',
            'message':message
        }
    )



# -------------------- Chat Notifications ---------------

@receiver(post_save, sender=Messages)
def notify_recipient_on_new_message(sender, instance, created, **kwargs):
    print('message sending ')
   
    if created:

        chat_room = instance.chat_room
        sender_user = instance.user
        print(chat_room)

        recipient_user = (
            chat_room.user2 if chat_room.user1 == sender_user else chat_room.user1
        )
    
        
        chat_room.last_message_timestamp = instance.timestamp
        chat_room.save()
        
        # Check if recipient is active in chat
        active_chats = cache.get(f'active_chats_{chat_room.id}', {})
        is_active = active_chats.get(recipient_user.id, False)
       
        if not is_active:
            message_content = {
                "type": "chat_notification",
                "content": instance.content,
                "username": f"{sender_user.username}",
                "recipient_user_id": recipient_user.id,
                "timestamp": instance.timestamp.isoformat(),
            }
            send_real_time_notification(recipient_user.id, message_content) 

        