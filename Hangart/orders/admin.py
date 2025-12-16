from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem, RefundRequest


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['added_at']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_items', 'total_price', 'created_at']
    search_fields = ['user__username', 'user__email']
    inlines = [CartItemInline]
    readonly_fields = ['created_at', 'updated_at']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['artwork', 'price', 'quantity']
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'buyer', 'status', 'total_amount',"commission", 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'buyer__username', 'buyer__email']
    readonly_fields = ['order_number', 'buyer', 'subtotal', 'commission', 'total_amount', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'buyer', 'status')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'payment_reference')
        }),
        ('Amounts', {
            'fields': ('subtotal', 'shipping_fee', 'commission', 'total_amount')
        }),
        ('Shipping', {
            'fields': ('shipping_address', 'tracking_number')
        }),
        ('Admin Notes', {
            'fields': ('admin_notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['mark_as_paid', 'mark_as_shipped']
    
    def mark_as_paid(self, request, queryset):
        queryset.update(status='paid')
        self.message_user(request, f"{queryset.count()} orders marked as paid.")
    mark_as_paid.short_description = "Mark selected orders as paid"
    
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')
        self.message_user(request, f"{queryset.count()} orders marked as shipped.")
    mark_as_shipped.short_description = "Mark selected orders as shipped"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'artwork', 'price', 'quantity']
    list_filter = ['order__status']
    search_fields = ['order__order_number', 'artwork__title']
    readonly_fields = ['order', 'artwork', 'price', 'quantity']


@admin.register(RefundRequest)
class RefundRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'buyer', 'reason', 'status', 'refund_amount', 'created_at']
    list_filter = ['status', 'reason', 'created_at']
    search_fields = ['order__order_number', 'buyer__username', 'buyer__email']
    readonly_fields = ['order', 'buyer', 'refund_amount', 'created_at', 'updated_at', 'reviewed_at']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('order', 'buyer', 'reason', 'description')
        }),
        ('Review', {
            'fields': ('status', 'admin_response', 'reviewed_by', 'reviewed_at')
        }),
        ('Financial', {
            'fields': ('refund_amount',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['approve_refund', 'reject_refund']
    
    def approve_refund(self, request, queryset):
        from django.utils import timezone
        pending = queryset.filter(status='pending')
        count = pending.count()
        
        for refund in pending:
            refund.status = 'approved'
            refund.reviewed_by = request.user
            refund.reviewed_at = timezone.now()
            refund.save()
            
            # Update order status
            refund.order.status = 'refunded'
            refund.order.save()
            
            # Make artworks available again
            for item in refund.order.items.all():
                artwork = item.artwork
                artwork.is_available = True
                artwork.status = 'approved'
                artwork.save()
        
        self.message_user(request, f"{count} refund request(s) approved.")
    approve_refund.short_description = "Approve selected refund requests"
    
    def reject_refund(self, request, queryset):
        from django.utils import timezone
        pending = queryset.filter(status='pending')
        count = pending.count()
        
        for refund in pending:
            refund.status = 'rejected'
            refund.reviewed_by = request.user
            refund.reviewed_at = timezone.now()
            refund.save()
        
        self.message_user(request, f"{count} refund request(s) rejected.")
    reject_refund.short_description = "Reject selected refund requests"
