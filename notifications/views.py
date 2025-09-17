from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import DeviceToken, PushNotification
from .firebase_service import FirebaseService
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_device_token(request):
    """
    Register or update a device token for push notifications
    
    Expected payload:
    {
        "token": "device_fcm_token",
        "device_type": "android|ios|web",
        "user_id": 1 (optional)
    }
    """
    try:
        token = request.data.get('token')
        device_type = request.data.get('device_type', 'android')
        user_id = request.data.get('user_id')
        
        if not token:
            return Response(
                {'error': 'Token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user if provided
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Create or update device token
        device_token, created = DeviceToken.objects.update_or_create(
            token=token,
            defaults={
                'user': user,
                'device_type': device_type,
                'is_active': True
            }
        )
        
        return Response({
            'message': 'Device token registered successfully',
            'created': created,
            'device_token_id': device_token.id
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error registering device token: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def unregister_device_token(request):
    """
    Unregister a device token
    
    Expected payload:
    {
        "token": "device_fcm_token"
    }
    """
    try:
        token = request.data.get('token')
        
        if not token:
            return Response(
                {'error': 'Token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        device_token = get_object_or_404(DeviceToken, token=token)
        device_token.is_active = False
        device_token.save()
        
        return Response({
            'message': 'Device token unregistered successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error unregistering device token: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def send_test_notification(request):
    """
    Send a test notification to a specific device token
    
    Expected payload:
    {
        "token": "device_fcm_token",
        "title": "Test Notification",
        "body": "This is a test notification",
        "data": {"key": "value"} (optional),
        "image_url": "https://example.com/image.png" (optional)
    }
    """
    try:
        token = request.data.get('token')
        title = request.data.get('title', 'Test Notification')
        body = request.data.get('body', 'This is a test notification')
        data = request.data.get('data', {})
        image_url = request.data.get('image_url')
        
        logger.info(f"Test notification request received:")
        logger.info(f"Token: {token[:20] if token else 'None'}...")
        logger.info(f"Title: {title}")
        logger.info(f"Body: {body}")
        
        if not token:
            return Response(
                {'error': 'Token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if Firebase is available
        if not FirebaseService.is_firebase_available():
            return Response({
                'error': 'Firebase is not configured. Please set up firebase-service-account-key.json',
                'details': 'Download the service account key from Firebase Console and place it in the project root'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Send notification
        response = FirebaseService.send_notification_to_token(
            token=token,
            title=title,
            body=body,
            data=data,
            image_url=image_url
        )
        
        if response['success']:
            logger.info(f"Test notification sent successfully: {response['message_id']}")
            return Response({
                'message': 'Test notification sent successfully',
                'message_id': response['message_id']
            }, status=status.HTTP_200_OK)
        else:
            logger.error(f"Failed to send test notification: {response['error']}")
            return Response({
                'error': f'Failed to send notification: {response["error"]}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error sending test notification: {str(e)}")
        return Response(
            {
                'error': 'Internal server error', 
                'details': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def test_connection(request):
    """
    Simple test endpoint to verify Django backend is working
    """
    try:
        from django.utils import timezone
        
        return Response({
            'message': 'Django backend is working!',
            'timestamp': timezone.now().isoformat(),
            'firebase_available': FirebaseService.is_firebase_available(),
            'endpoints': {
                'register': '/api/notifications/register/',
                'unregister': '/api/notifications/unregister/',
                'test': '/api/notifications/test/',
                'mock_test': '/api/notifications/mock-test/',
                'connection_test': '/api/notifications/test-connection/'
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Backend error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def mock_send_notification(request):
    """
    Mock notification sending for testing without Firebase
    """
    try:
        token = request.data.get('token')
        title = request.data.get('title', 'Test Notification')
        body = request.data.get('body', 'This is a test notification')
        
        logger.info(f"Mock notification request:")
        logger.info(f"Token: {token[:20] if token else 'None'}...")
        logger.info(f"Title: {title}")
        logger.info(f"Body: {body}")
        
        if not token:
            return Response(
                {'error': 'Token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Simulate successful notification
        mock_message_id = f"mock-message-{hash(token + title + body)}"
        
        return Response({
            'message': 'Mock notification sent successfully (Firebase not configured)',
            'message_id': mock_message_id,
            'note': 'This is a mock response. To send real notifications, configure Firebase.'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in mock notification: {str(e)}")
        return Response(
            {'error': 'Internal server error', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
