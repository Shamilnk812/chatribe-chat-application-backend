from django.urls import path
from .views import *


urlpatterns = [
    path('add-chat-rooms/', AddChatRoomView.as_view(), name='add-chat-room'),
    path('get-chat-users/<int:user_id>/',ListChatUsersView.as_view(),name='get-chat-users'),
    path('get-single-chat-user/<int:chat_room_id>/',GetSingleChatUserView.as_view(),name='get-single-chat-user'),
    path('get-messages/<int:user_id1>/<int:user_id2>/',GetMessagesView.as_view(),name='get-messages'),
    path('send-interest-request/',SendInterestView.as_view(),name='send-interest-request'),
    path('handle-interest-request/',HandleInterestView.as_view(),name='handle-intrest-request'),
    path('get-interest-request/',ListInterestRequestsView.as_view(),name='get-interest-request'),
]