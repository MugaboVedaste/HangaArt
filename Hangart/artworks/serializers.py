from rest_framework import serializers
from .models import Artwork
from accounts.serializers import UserSerializer


class ArtworkSerializer(serializers.ModelSerializer):
    artist = UserSerializer(read_only=True)
    artist_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Artwork
        fields = [
            'id', 'artist', 'artist_id', 'title', 'slug', 'description',
            'category', 'medium', 'width_cm', 'height_cm', 'depth_cm',
            'creation_year', 'price', 'is_available', 'main_image',
            'additional_images', 'status', 'admin_comment',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at', 'admin_comment']
    
    def create(self, validated_data):
        # Set the artist to the current user
        validated_data['artist'] = self.context['request'].user
        validated_data.pop('artist_id', None)  # Remove artist_id if present
        return super().create(validated_data)


class ArtworkListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views"""
    artist_name = serializers.CharField(source='artist.username', read_only=True)
    artist_id = serializers.IntegerField(source='artist.id', read_only=True)
    
    class Meta:
        model = Artwork
        fields = [
            'id', 'artist_id', 'artist_name', 'title', 'slug',
            'category', 'medium', 'price', 'is_available',
            'main_image', 'status', 'created_at'
        ]


class ArtworkStatusUpdateSerializer(serializers.ModelSerializer):
    """Admin-only serializer for updating artwork status and comments"""
    class Meta:
        model = Artwork
        fields = ['status', 'admin_comment']
    
    def validate_status(self, value):
        allowed_statuses = ['approved', 'rejected', 'archived']
        if value not in allowed_statuses:
            raise serializers.ValidationError(
                f"Admin can only set status to: {', '.join(allowed_statuses)}"
            )
        return value
