from .models import * 
from rest_framework import serializers
from users.serializers import GetAllUserSerializer

class ChatRoomSerializer(serializers.ModelSerializer):
    user1 = GetAllUserSerializer(read_only=True)
    user2 = GetAllUserSerializer(read_only=True)
    # last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatRooms
        fields = ['id', 'user1', 'user2', 'created_at', 'last_message_timestamp']

    # def get_last_message(self, obj):
    #     last_message = obj.messages.last()
    #     if last_message:
    #         return {
    #             'content': last_message.content,
    #             'timestamp': last_message.timestamp,
    #             'seen': last_message.seen
    #         }
    #     return None

class MessageSerializer(serializers.ModelSerializer):
    user = GetAllUserSerializer(read_only=True)

    class Meta:
        model = Messages
        fields = ['id', 'chat_room', 'user', 'content', 'timestamp', 'seen']


class InterestRequestSerializer(serializers.ModelSerializer):
    sender = GetAllUserSerializer(read_only=True)
    receiver = GetAllUserSerializer(read_only=True)
    
    class Meta:
        model = InterestRequest
        fields = ['id', 'sender', 'receiver', 'status', 'created_at']
        read_only_fields = ['id', 'created_at', 'updated_at']