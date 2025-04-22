from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import generics,status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import authenticate
from django.db.models import Q

from .models import User
from .serializers import *


# Create your views here.


# ----------------- User Registration ---------------------


class UserRegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserRegisterSerializer

    def post(self, request):
        print('data is ',request.data)
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            user_token = user.generate_token()
            
            return Response({
                'user_id': str(user.id),
                'access_token': user_token.get('access_token'),
                'refresh_token' : user_token.get('refresh_token')
            },status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    
class UserLoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password :
            raise AuthenticationFailed('Email and password are required')

        user = authenticate(request, email=email, password=password)
        if not user :
            raise AuthenticationFailed('Invalid credentials')
        
        if  user.is_superuser:
            raise AuthenticationFailed('Only valid user can loging ')

        user_token = user.generate_token()    
        return Response({
            'user_id': str(user.id),
            'access_token': user_token.get('access_token'),
            'refresh_token' : user_token.get('refresh_token'),
            'message':"it is working brother keep hoing"
        },status=status.HTTP_200_OK)
    


class UserLogoutView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token :
            return Response({'error': 'Refresh token is required'},status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Successfully logged out'}, status=status.HTTP_205_RESET_CONTENT)
        
        except TokenError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)   



# ----------------------- Get all users ---------------

class GetAllUsersView(generics.ListAPIView):
    serializer_class = GetAllUserSerializer

    def get_queryset(self):
        user_id = self.kwargs.get("user_id")
        search_query = self.request.query_params.get('search', '').strip()
        queryset = User.objects.exclude(Q(id=user_id) | Q(is_superuser=True))

        if search_query :
            queryset = queryset.filter(username__icontains=search_query)
        return queryset     
    
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user_id'] = self.kwargs.get("user_id")  
        return context