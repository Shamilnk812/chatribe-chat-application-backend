from django.urls import path
from .views import *


urlpatterns = [
    path('add-chat-rooms/', AddChatRoomView.as_view(), name='add-chat-room'),
    path('get-chat-users/<int:user_id>/',ListChatUsersView.as_view(),name='get-chat-users'),
    path('get-messages/<int:user_id1>/<int:user_id2>/',GetMessagesView.as_view(),name='get-messages'),
]