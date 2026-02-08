from django.shortcuts import render
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.models import User
from core.models import Profile, PrefMenu
#from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
#from rest_framework_simplejwt.views import TokenObtainPairView

# Create user
"""
class UserSerializer(serializers.ModelSerializer):
    email=serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username=serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password=serializers.CharField(min_length=5)

    def create(self, validated_data):
        user=User.objects.create_user(validated_data['email'][0:30], 
        validated_data['email'], validated_data['password'])
        return user

    class Meta:
        model=User
        fields= ('id','username','email','password')
"""

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model=Profile
        fields = '__all__'

class PrefMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model=PrefMenu
        fields = '__all__'

