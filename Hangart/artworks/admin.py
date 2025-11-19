from django.contrib import admin
from .models import Artwork


@admin.register(Artwork)
class ArtworkAdmin(admin.ModelAdmin):
    list_display = ['title', 'artist', 'category', 'price', 'status', 'is_available', 'created_at']
    list_filter = ['status', 'category', 'medium', 'is_available']
    search_fields = ['title', 'artist__username', 'description']
    readonly_fields = ['slug', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('artist', 'title', 'slug', 'description')
        }),
        ('Classification', {
            'fields': ('category', 'medium')
        }),
        ('Dimensions', {
            'fields': ('width_cm', 'height_cm', 'depth_cm', 'creation_year')
        }),
        ('Pricing & Availability', {
            'fields': ('price', 'is_available')
        }),
        ('Media', {
            'fields': ('main_image', 'additional_images')
        }),
        ('Status & Approval', {
            'fields': ('status', 'admin_comment')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['approve_artworks', 'reject_artworks']
    
    def approve_artworks(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, f"{queryset.count()} artworks approved.")
    approve_artworks.short_description = "Approve selected artworks"
    
    def reject_artworks(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f"{queryset.count()} artworks rejected.")
    reject_artworks.short_description = "Reject selected artworks"
