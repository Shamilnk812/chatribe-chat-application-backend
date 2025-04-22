from rest_framework import serializers
from .models import User
from chat.models import InterestRequest
from django.db.models import Q

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password']


    def validate(self, attrs):
        email = attrs.get('email', '')
        
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("User with this email already exists.")
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Password do not match.")
        return attrs  
    

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user
    

class GetAllUserSerializer(serializers.ModelSerializer):
    interest_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_active', 'profile_picture', 'interest_status']

    def get_interest_status(self, obj):
        request_user_id = self.context.get('user_id')
        if not request_user_id:
            return None

        try:
            request_user = User.objects.get(id=request_user_id)
            interest = InterestRequest.objects.filter(
                Q(sender=request_user, receiver=obj) |
                Q(sender=obj, receiver=request_user)
            ).first()
            if interest:
                return {
                    "id": interest.id,  
                    "status": interest.status,
                    "sent_by_me": interest.sender_id == request_user_id
                }
            return None
        except User.DoesNotExist:
            return None
