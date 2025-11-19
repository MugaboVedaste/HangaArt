from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ArtistProfile, BuyerProfile, AdminProfile


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'is_verified', 'join_date']
    list_filter = ['role', 'is_verified', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'phone', 'is_verified')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('role', 'phone')}),
    )


@admin.register(ArtistProfile)
class ArtistProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialization', 'verified_by_admin', 'country', 'city']
    list_filter = ['verified_by_admin', 'country']
    search_fields = ['user__username', 'user__email', 'specialization']
    readonly_fields = ['user']


@admin.register(BuyerProfile)
class BuyerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'country', 'phone']
    list_filter = ['country']
    search_fields = ['user__username', 'user__email', 'city']
    readonly_fields = ['user']


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'employee_id', 'position']
    search_fields = ['user__username', 'employee_id']
    readonly_fields = ['user']
