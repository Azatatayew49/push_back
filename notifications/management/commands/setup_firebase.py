from django.core.management.base import BaseCommand
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Setup Firebase configuration for push notifications'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Firebase Push Notification Setup Instructions')
        )
        self.stdout.write('=' * 60)
        
        self.stdout.write('\n1. Go to Firebase Console (https://console.firebase.google.com/)')
        self.stdout.write('2. Select your project')
        self.stdout.write('3. Go to Project Settings (gear icon)')
        self.stdout.write('4. Navigate to "Service accounts" tab')
        self.stdout.write('5. Click "Generate new private key"')
        self.stdout.write('6. Download the JSON file')
        
        expected_path = settings.FIREBASE_SERVICE_ACCOUNT_KEY
        self.stdout.write(f'\n7. Place the downloaded file at: {expected_path}')
        
        if os.path.exists(expected_path):
            self.stdout.write(
                self.style.SUCCESS(f'✓ Firebase service account key found at {expected_path}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'✗ Firebase service account key not found at {expected_path}')
            )
            self.stdout.write('   Please download and place the service account key file.')
        
        self.stdout.write('\n8. Ensure your Firebase project has FCM enabled')
        self.stdout.write('9. Add your Flutter app to the Firebase project')
        self.stdout.write('10. Download google-services.json (Android) and GoogleService-Info.plist (iOS)')
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('Setup complete! You can now send push notifications from Django admin.')
        
        # Test Firebase initialization
        try:
            from notifications.firebase_service import FirebaseService
            FirebaseService.initialize_firebase()
            self.stdout.write(
                self.style.SUCCESS('✓ Firebase service initialized successfully!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Firebase initialization failed: {str(e)}')
            )
