from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib import messages
from django.db import transaction
from .models import PushNotification, DeviceToken, NotificationLog
from .firebase_service import FirebaseService
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=PushNotification)
def auto_send_notification(sender, instance, created, **kwargs):
    """
    Automatically send push notification when it's created and auto_send is True
    """
    if created and instance.status == 'draft' and instance.auto_send:
        # Use transaction.on_commit to ensure the notification is saved first
        transaction.on_commit(lambda: send_notification_async(instance.id))


def send_notification_async(notification_id):
    """
    Send notification asynchronously
    """
    try:
        notification = PushNotification.objects.get(id=notification_id)
        
        # Update status to sending
        notification.status = 'sending'
        notification.save()
        
        # Get target device tokens
        target_tokens = get_target_tokens(notification)
        
        if not target_tokens:
            notification.status = 'failed'
            notification.save()
            logger.error(f"No valid device tokens found for notification {notification.id}")
            return
        
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
        
        logger.info(
            f"Notification '{notification.title}' sent automatically! "
            f"Success: {success_count}, Failed: {failure_count}"
        )
        
    except Exception as e:
        logger.error(f"Failed to send notification {notification_id}: {str(e)}")
        try:
            notification = PushNotification.objects.get(id=notification_id)
            notification.status = 'failed'
            notification.save()
        except:
            pass


def get_target_tokens(notification):
    """Get device tokens based on targeting criteria"""
    queryset = DeviceToken.objects.filter(is_active=True)
    
    # Filter by device type
    if notification.target_device_types != 'all':
        queryset = queryset.filter(device_type=notification.target_device_types)
    
    # Filter by users
    if not notification.send_to_all and notification.target_users.exists():
        queryset = queryset.filter(user__in=notification.target_users.all())
    
    return list(queryset)
