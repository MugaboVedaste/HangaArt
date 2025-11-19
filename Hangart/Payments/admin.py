from django.contrib import admin
from .models import PaymentTransaction, PaymentLog


class PaymentLogInline(admin.TabularInline):
    model = PaymentLog
    extra = 0
    readonly_fields = ['message', 'timestamp']
    can_delete = False


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'user', 'order', 'payment_method', 'amount', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['transaction_id', 'user__username', 'order__order_number']
    readonly_fields = ['transaction_id', 'user', 'order', 'amount', 'created_at', 'updated_at']
    inlines = [PaymentLogInline]
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('transaction_id', 'user', 'order')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'amount', 'status')
        }),
        ('Gateway Data', {
            'fields': ('provider_response',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['mark_as_successful', 'mark_as_failed']
    
    def mark_as_successful(self, request, queryset):
        queryset.update(status='successful')
        self.message_user(request, f"{queryset.count()} payments marked as successful.")
    mark_as_successful.short_description = "Mark selected payments as successful"
    
    def mark_as_failed(self, request, queryset):
        queryset.update(status='failed')
        self.message_user(request, f"{queryset.count()} payments marked as failed.")
    mark_as_failed.short_description = "Mark selected payments as failed"


@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ['payment', 'message', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['payment__transaction_id', 'message']
    readonly_fields = ['payment', 'message', 'timestamp']
