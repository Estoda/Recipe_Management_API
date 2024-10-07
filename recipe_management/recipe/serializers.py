from rest_framework import serializers
from .models import Recipe, User
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'is_superuser']
        read_only_fields = ['is_superuser']
        extra_kwargs = {
            'password': {'write_only': True}
        }


    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email']
            )
        user.set_password(validated_data['password'])
        user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ['created_at']

    def validate(self, data):
        if not data.get('title'):
            raise serializers.ValidationError({'title': 'This Field is required !'})
        if not data.get('ingredients'):
            raise serializers.ValidationError({'ingredients': 'This Field is required !'})
        if not data.get('instructions'):
            raise serializers.ValidationError({'instructions': 'This Field is required !'})
        return data
