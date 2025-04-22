from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import traceback
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from .models import * 
from django.utils.timezone import now
from .serializers import ChatRoomSerializer,MessageSerializer,InterestRequestSerializer
from django.db.models import Q
from .signals import send_real_time_notification



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



class SendInterestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        
        receiver_id = request.data.get('receiver_id')

        if not receiver_id :
            return Response({'error': 'Receiver ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if request.user.id == receiver_id :
            return Response({'error': 'Cannot send interest to yourself'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            receiver = User.objects.get(id=receiver_id)

        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        existing_request = InterestRequest.objects.filter(
            sender = request.user,
            receiver = receiver
        ).first()

        if existing_request :
            existing_request.status = 'pending'
            existing_request.save()
            serializer = InterestRequestSerializer(existing_request)

            send_real_time_notification(
                receiver.id,
                {
                    "type": "interest_notification",
                    "content": f"{request.user.username} sent you an interest request.",
                    "username": f"{request.user.username}",
                    "timestamp": now().isoformat(),
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        

        interest_request = InterestRequest.objects.create(
            sender=request.user,
            receiver=receiver,
            status="pending"
        )

        send_real_time_notification(
                receiver.id,
                {
                    "type": "interest_notification",
                    "content": f"{request.user.username} sent you an interest request.",
                    "username": f"{request.user.username}",
                    "timestamp": now().isoformat(),
                }
            )
        serializer = InterestRequestSerializer(interest_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)




class HandleInterestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request_id = request.data.get('interest_id')
        action = request.data.get('action')  
        print('req', request)
        print('actio',action)
        
        if action not in ['accepted', 'rejected']:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            interest_request = InterestRequest.objects.get(
                id=request_id,
                receiver=request.user,
            )
        except InterestRequest.DoesNotExist:
            return Response({'error': 'Interest request not found'}, status=status.HTTP_404_NOT_FOUND)
        

        interest_request.status = action
        interest_request.save()

        # Prepare the message content
        content_map = {
            "accepted": f"{interest_request.receiver.username} accepted your interest request.",
            "rejected": f"{interest_request.receiver.username} rejected your interest request.",
        }

        notification_payload = {
            "type": "interest_notification",
            "content": content_map[action],
            "username": f"{interest_request.receiver.username}",
            "timestamp": now().isoformat(),
        }

       
        send_real_time_notification(interest_request.sender.id, notification_payload)

        return Response({'message': f'Interest request {action}'}, status=status.HTTP_200_OK)
        


class ListInterestRequestsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pending_requests = InterestRequest.objects.filter(
            receiver=request.user,
            status='pending'
        ).order_by('-created_at')
        
        serializer = InterestRequestSerializer(pending_requests, many=True)
        return Response(serializer.data)






