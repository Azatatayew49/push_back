from django.db import models
from django.contrib.auth.models import User


class DeviceToken(models.Model):
    """Model to store FCM device tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    token = models.TextField(unique=True)
    device_type = models.CharField(max_length=20, choices=[
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('web', 'Web')
    ], default='android')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.device_type} - {self.token[:20]}..."

    class Meta:
        verbose_name = "Device Token"
        verbose_name_plural = "Device Tokens"


class PushNotification(models.Model):
    """Model to store push notifications"""
    title = models.CharField(max_length=255)
    body = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    image_url = models.URLField(blank=True, null=True)
    
    # Send immediately option
    auto_send = models.BooleanField(
        default=True, 
        help_text="Send notification immediately after saving"
    )
    
    # Targeting options
    send_to_all = models.BooleanField(default=True)
    target_users = models.ManyToManyField(User, blank=True)
    target_device_types = models.CharField(
        max_length=50, 
        choices=[
            ('all', 'All Devices'),
            ('android', 'Android Only'),
            ('ios', 'iOS Only'),
            ('web', 'Web Only')
        ], 
        default='all'
    )
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed')
    ], default='draft')
    
    total_recipients = models.IntegerField(default=0)
    successful_sends = models.IntegerField(default=0)
    failed_sends = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_notifications')

    def __str__(self):
        return f"{self.title} - {self.status}"

    class Meta:
        verbose_name = "Push Notification"
        verbose_name_plural = "Push Notifications"
        ordering = ['-created_at']


class NotificationLog(models.Model):
    """Model to log individual notification sends"""
    notification = models.ForeignKey(PushNotification, on_delete=models.CASCADE, related_name='logs')
    device_token = models.ForeignKey(DeviceToken, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('failed', 'Failed')
    ])
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.notification.title} - {self.device_token.token[:20]}... - {self.status}"

    class Meta:
        verbose_name = "Notification Log"
        verbose_name_plural = "Notification Logs"
