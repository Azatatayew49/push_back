import firebase_admin
from firebase_admin import credentials, messaging
import json
import os
from django.conf import settings
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class FirebaseService:
    """Service class to handle Firebase push notifications"""
    
    _app = None
    _initialized = False
    
    @classmethod
    def initialize_firebase(cls):
        """Initialize Firebase Admin SDK"""
        if cls._app is None and not cls._initialized:
            try:
                # Path to your Firebase service account key file
                service_account_path = getattr(settings, 'FIREBASE_SERVICE_ACCOUNT_KEY', None)
                
                if service_account_path and os.path.exists(service_account_path):
                    cred = credentials.Certificate(service_account_path)
                    cls._app = firebase_admin.initialize_app(cred)
                    cls._initialized = True
                    logger.info("Firebase initialized successfully with service account key")
                else:
                    logger.error(f"Firebase service account key not found at: {service_account_path}")
                    logger.error("Firebase features will be disabled")
                    cls._initialized = True  # Mark as initialized to avoid repeated attempts
                    
            except Exception as e:
                logger.error(f"Failed to initialize Firebase: {str(e)}")
                cls._initialized = True  # Mark as initialized to avoid repeated attempts
                raise e
    
    @classmethod
    def is_firebase_available(cls):
        """Check if Firebase is properly initialized"""
        cls.initialize_firebase()
        return cls._app is not None
    
    @classmethod
    def send_notification_to_token(
        cls, 
        token: str, 
        title: str, 
        body: str, 
        data: Optional[Dict[str, Any]] = None,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a push notification to a single device token
        
        Args:
            token: FCM device token
            title: Notification title
            body: Notification body
            data: Additional data payload
            image_url: Optional image URL
            
        Returns:
            Dict with success status and message_id or error
        """
        if not cls.is_firebase_available():
            logger.error("Firebase is not available. Cannot send notification.")
            return {
                'success': False,
                'message_id': None,
                'error': 'Firebase is not properly configured. Please check your service account key.'
            }
        
        try:
            # Create notification
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url
            )
            
            # Create message
            message = messaging.Message(
                notification=notification,
                data=data or {},
                token=token,
            )
            
            # Send message
            response = messaging.send(message)
            logger.info(f"Successfully sent message: {response}")
            
            return {
                'success': True,
                'message_id': response,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Failed to send notification to token {token}: {str(e)}")
            return {
                'success': False,
                'message_id': None,
                'error': str(e)
            }
    
    @classmethod
    def send_notification_to_multiple_tokens(
        cls, 
        tokens: List[str], 
        title: str, 
        body: str, 
        data: Optional[Dict[str, Any]] = None,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a push notification to multiple device tokens
        
        Args:
            tokens: List of FCM device tokens
            title: Notification title
            body: Notification body
            data: Additional data payload
            image_url: Optional image URL
            
        Returns:
            Dict with success/failure counts and details
        """
        cls.initialize_firebase()
        
        if not tokens:
            return {
                'success_count': 0,
                'failure_count': 0,
                'responses': []
            }
        
        try:
            # Create notification
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url
            )
            
            # Send to each token individually (more compatible approach)
            responses = []
            success_count = 0
            failure_count = 0
            
            for token in tokens:
                try:
                    # Create individual message
                    message = messaging.Message(
                        notification=notification,
                        data=data or {},
                        token=token,
                    )
                    
                    # Send individual message
                    message_id = messaging.send(message)
                    
                    responses.append({
                        'token': token,
                        'success': True,
                        'message_id': message_id,
                        'error': None
                    })
                    success_count += 1
                    
                except Exception as e:
                    responses.append({
                        'token': token,
                        'success': False,
                        'message_id': None,
                        'error': str(e)
                    })
                    failure_count += 1
            
            logger.info(f"Successfully sent {success_count} messages")
            logger.info(f"Failed to send {failure_count} messages")
            
            return {
                'success_count': success_count,
                'failure_count': failure_count,
                'responses': responses
            }
            
        except Exception as e:
            logger.error(f"Failed to send multicast notification: {str(e)}")
            return {
                'success_count': 0,
                'failure_count': len(tokens),
                'responses': [
                    {
                        'token': token,
                        'success': False,
                        'message_id': None,
                        'error': str(e)
                    } for token in tokens
                ]
            }
    
    @classmethod
    def send_notification_to_topic(
        cls, 
        topic: str, 
        title: str, 
        body: str, 
        data: Optional[Dict[str, Any]] = None,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a push notification to a topic
        
        Args:
            topic: FCM topic name
            title: Notification title
            body: Notification body
            data: Additional data payload
            image_url: Optional image URL
            
        Returns:
            Dict with success status and message_id or error
        """
        cls.initialize_firebase()
        
        try:
            # Create notification
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url
            )
            
            # Create message
            message = messaging.Message(
                notification=notification,
                data=data or {},
                topic=topic,
            )
            
            # Send message
            response = messaging.send(message)
            logger.info(f"Successfully sent message to topic {topic}: {response}")
            
            return {
                'success': True,
                'message_id': response,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Failed to send notification to topic {topic}: {str(e)}")
            return {
                'success': False,
                'message_id': None,
                'error': str(e)
            }
