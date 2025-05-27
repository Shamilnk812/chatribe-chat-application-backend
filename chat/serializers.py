from .models import * 
from rest_framework import serializers
from users.serializers import GetAllUserSerializer

class ChatRoomSerializer(serializers.ModelSerializer):
    user1 = GetAllUserSerializer(read_only=True)
    user2 = GetAllUserSerializer(read_only=True)
    unread_count_user1 = serializers.SerializerMethodField()
    unread_count_user2 = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatRooms
        fields = ['id', 'user1', 'user2', 'created_at', 'last_message_timestamp', 'unread_count_user1', 'unread_count_user2', 'last_message']
    
    
    def get_unread_count_user1(self, obj):
        user = self.context.get('user')
        if user == obj.user1.id:
            return obj.message.filter(seen=False).exclude(user=obj.user1).count()
    

    def get_unread_count_user2(self, obj):
        user = self.context.get('user')
        if user == obj.user2.id:
            return obj.message.filter(seen=False).exclude(user=obj.user2).count()

    def get_last_message(self, obj):
        last_message = obj.message.order_by('-timestamp').first()
        return last_message.content if last_message else ""
        



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