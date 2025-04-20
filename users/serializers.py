from rest_framework import serializers
from .models import User


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
    class Meta:
        model = User
        fields = '__all__'

