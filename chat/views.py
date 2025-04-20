from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import traceback
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from .models import * 
from .serializers import ChatRoomSerializer,MessageSerializer
from django.db.models import Q



class AddChatRoomView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user_id1 = request.data.get('user_id1')
            user_id2 = request.data.get('user_id2')
            print(user_id1, user_id2, '00000')

            if user_id1 == user_id2:
                return Response({'error': 'Cannot create chat room with the same user.'}, status=status.HTTP_400_BAD_REQUEST)
            
            chat_rooms = ChatRooms.objects.filter(
                Q(user1_id=user_id1, user2_id=user_id2) | Q(user1_id=user_id2, user2_id=user_id1)

            )

            if chat_rooms.exists() :
                chat_room = chat_rooms.first()
                serializer = ChatRoomSerializer(chat_room)
                return Response(serializer.data, status=status.HTTP_200_OK)
            
            else :
                chat_room = ChatRooms.objects.create(user1_id=user_id1, user2_id=user_id2)
                serializer = ChatRoomSerializer(chat_room)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e :
            traceback.print_exc()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class ListChatUsersView(APIView):
    
    def get(self, request, user_id):
        try :
            users = ChatRooms.objects.filter(Q(user1_id = user_id) | Q(user2_id = user_id)).order_by('-last_message_timestamp')
            if not users:
                return Response({'message':'No chat rooms found '})
            serializer = ChatRoomSerializer(users, many = True, context={'user': user_id})
            return Response(serializer.data) 
        
        except ChatRooms.DoesNotExist :
            return ChatRooms.objects.none()



class GetMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id1, user_id2):
        print('user id 1', user_id1)
        print('user id 2', user_id2)

        try:

            chat_room = ChatRooms.objects.filter(
                Q(user1_id=user_id1, user2_id=user_id2) | Q(user1_id=user_id2, user2_id=user_id1)
            ).first()  

            if not chat_room :
                raise NotFound('Room not found')
            
            messages = Messages.objects.filter(chat_room=chat_room).order_by('-timestamp')
            messages.filter(seen=False).exclude(user=request.user).update(seen=True)

            serializer = MessageSerializer(messages, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except ChatRooms.DoesNotExist:
            return Response({'detail': 'Chat room does not exist'}, status=status.HTTP_404_NOT_FOUND)



