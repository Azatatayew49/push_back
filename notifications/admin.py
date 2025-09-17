from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.utils import timezone
from django.db import transaction
from .models import DeviceToken, PushNotification, NotificationLog
from .firebase_service import FirebaseService
import json


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'device_type', 'token_preview', 'is_active', 'created_at']
    list_filter = ['device_type', 'is_active', 'created_at']
    search_fields = ['token', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    def token_preview(self, obj):
        return f"{obj.token[:20]}..." if obj.token else ""
    token_preview.short_description = "Token Preview"


@admin.register(PushNotification)
class PushNotificationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title', 'status', 'total_recipients', 
        'successful_sends', 'failed_sends', 'created_at', 'sent_at'
    ]
    list_filter = ['status', 'target_device_types', 'send_to_all', 'created_at']
    search_fields = ['title', 'body']
    readonly_fields = [
        'status', 'total_recipients', 'successful_sends', 
        'failed_sends', 'created_at', 'sent_at', 'created_by'
    ]
    filter_horizontal = ['target_users']
    
    fieldsets = (
        ('Notification Content', {
            'fields': ('title', 'body', 'image_url', 'data')
        }),
        ('Send Options', {
            'fields': ('auto_send',)
        }),
        ('Targeting', {
            'fields': ('send_to_all', 'target_device_types', 'target_users')
        }),
        ('Status & Statistics', {
            'fields': (
                'status', 'total_recipients', 'successful_sends', 
                'failed_sends', 'created_at', 'sent_at', 'created_by'
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['send_notifications']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def send_notifications(self, request, queryset):
        """Action to send selected notifications"""
        sent_count = 0
        error_count = 0
        
        for notification in queryset.filter(status='draft'):
            try:
                with transaction.atomic():
                    self._send_single_notification(notification, request)
                    sent_count += 1
            except Exception as e:
                error_count += 1
                messages.error(
                    request,
                    f"Failed to send notification '{notification.title}': {str(e)}"
                )
        
        if sent_count > 0:
            messages.success(
                request,
                f"Successfully sent {sent_count} notification(s)"
            )
        
        if error_count > 0:
            messages.error(
                request,
                f"Failed to send {error_count} notification(s)"
            )
    
    send_notifications.short_description = "Send selected notifications"
    
    def _send_single_notification(self, notification, request):
        """Send a single notification"""
        # Update status to sending
        notification.status = 'sending'
        notification.save()
        
        # Get target device tokens
        target_tokens = self._get_target_tokens(notification)
        
        if not target_tokens:
            notification.status = 'failed'
            notification.save()
            raise Exception("No valid device tokens found for targeting criteria")
        
        notification.total_recipients = len(target_tokens)
        notification.save()
        
        # Prepare notification data
        data = notification.data if notification.data else {}
        
        # Send notifications
        success_count = 0
        failure_count = 0
        
        # Send in batches of 500 (FCM limit)
        batch_size = 500
        for i in range(0, len(target_tokens), batch_size):
            batch_tokens = target_tokens[i:i + batch_size]
            
            response = FirebaseService.send_notification_to_multiple_tokens(
                tokens=[token.token for token in batch_tokens],
                title=notification.title,
                body=notification.body,
                data=data,
                image_url=notification.image_url
            )
            
            # Log individual responses
            for idx, resp in enumerate(response['responses']):
                token = batch_tokens[idx]
                
                NotificationLog.objects.create(
                    notification=notification,
                    device_token=token,
                    status='success' if resp['success'] else 'failed',
                    error_message=resp['error'] if not resp['success'] else None
                )
                
                if resp['success']:
                    success_count += 1
                else:
                    failure_count += 1
        
        # Update notification status
        notification.successful_sends = success_count
        notification.failed_sends = failure_count
        notification.sent_at = timezone.now()
        
        if success_count > 0:
            notification.status = 'sent'
        else:
            notification.status = 'failed'
        
        notification.save()
        
        messages.success(
            request,
            f"Notification '{notification.title}' sent successfully! "
            f"Success: {success_count}, Failed: {failure_count}"
        )
    
    def _get_target_tokens(self, notification):
        """Get device tokens based on targeting criteria"""
        queryset = DeviceToken.objects.filter(is_active=True)
        
        # Filter by device type
        if notification.target_device_types != 'all':
            queryset = queryset.filter(device_type=notification.target_device_types)
        
        # Filter by users
        if not notification.send_to_all and notification.target_users.exists():
            queryset = queryset.filter(user__in=notification.target_users.all())
        
        return list(queryset)


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'notification', 'device_token_preview', 
        'status', 'sent_at', 'error_preview'
    ]
    list_filter = ['status', 'sent_at', 'notification__title']
    search_fields = [
        'notification__title', 'device_token__token', 
        'error_message'
    ]
    readonly_fields = [
        'notification', 'device_token', 'status', 
        'error_message', 'sent_at'
    ]
    
    def device_token_preview(self, obj):
        return f"{obj.device_token.token[:20]}..." if obj.device_token.token else ""
    device_token_preview.short_description = "Device Token"
    
    def error_preview(self, obj):
        if obj.error_message:
            return format_html(
                '<span style="color: red;">{}</span>',
                obj.error_message[:50] + '...' if len(obj.error_message) > 50 else obj.error_message
            )
        return "-"
    error_preview.short_description = "Error"
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation
    
    def has_change_permission(self, request, obj=None):
        return False  # Make read-only
