from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ArtistProfile, BuyerProfile, AdminProfile

User = get_user_model()


class ArtistProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    
    class Meta:
        model = ArtistProfile
        fields = [
            'id', 'user_id', 'username', 'bio', 'profile_photo', 'website', 'specialization',
            'experience_years', 'phone', 'email', 'country', 'city',
            'verified_by_admin', 'instagram', 'facebook', 'twitter_x',
            'youtube', 'tiktok', 'linkedin'
        ]
        read_only_fields = ['verified_by_admin']


class BuyerProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = BuyerProfile
        fields = [
            'id', 'user_id', 'username', 'email', 'profile_photo', 'phone',
            'address', 'city', 'country', 'date_of_birth'
        ]


class AdminProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminProfile
        fields = ['id', 'employee_id', 'position', 'phone', 'email']


class UserSerializer(serializers.ModelSerializer):
    artist_profile = ArtistProfileSerializer(read_only=True)
    buyer_profile = BuyerProfileSerializer(read_only=True)
    admin_profile = AdminProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'phone', 'is_verified', 'join_date',
            'artist_profile', 'buyer_profile', 'admin_profile'
        ]
        read_only_fields = ['is_verified', 'join_date']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, label='Confirm Password', style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name', 'role', 'phone']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        if attrs['role'] not in ['artist', 'buyer']:
            raise serializers.ValidationError({"role": "Role must be either 'artist' or 'buyer' for registration."})
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create corresponding profile
        if user.role == 'artist':
            ArtistProfile.objects.create(user=user)
        elif user.role == 'buyer':
            BuyerProfile.objects.create(user=user)
        
        return user


class ArtistVerificationSerializer(serializers.ModelSerializer):
    """Admin-only serializer for verifying artists"""
    class Meta:
        model = ArtistProfile
        fields = ['verified_by_admin']


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password2 = serializers.CharField(required=True, write_only=True, label='Confirm New Password', style={'input_type': 'password'})
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "New password fields didn't match."})
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
