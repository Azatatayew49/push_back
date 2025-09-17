from django.core.management.base import BaseCommand
import json
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Create a demo Firebase service account file for testing (without real credentials)'

    def handle(self, *args, **options):
        demo_config = {
            "type": "service_account",
            "project_id": "your-project-id",
            "private_key_id": "demo-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\nDEMO_KEY_CONTENT\n-----END PRIVATE KEY-----\n",
            "client_email": "firebase-adminsdk-xxxxx@your-project-id.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40your-project-id.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com"
        }
        
        file_path = settings.FIREBASE_SERVICE_ACCOUNT_KEY
        
        # Create demo file
        with open(file_path, 'w') as f:
            json.dump(demo_config, f, indent=2)
        
        self.stdout.write(
            self.style.WARNING(f'Created demo Firebase service account file at: {file_path}')
        )
        self.stdout.write(
            self.style.WARNING('⚠️  This is a DEMO file with fake credentials!')
        )
        self.stdout.write(
            self.style.WARNING('⚠️  Replace it with your real Firebase service account key.')
        )
        self.stdout.write('')
        self.stdout.write('To get your real Firebase service account key:')
        self.stdout.write('1. Go to https://console.firebase.google.com/')
        self.stdout.write('2. Select your project')
        self.stdout.write('3. Go to Project Settings → Service accounts')
        self.stdout.write('4. Click "Generate new private key"')
        self.stdout.write('5. Replace the demo file with the downloaded JSON file')
        
        # Test Firebase initialization
        self.stdout.write('\nTesting Firebase initialization...')
        try:
            from notifications.firebase_service import FirebaseService
            if FirebaseService.is_firebase_available():
                self.stdout.write(self.style.SUCCESS('✓ Firebase service file detected'))
            else:
                self.stdout.write(self.style.ERROR('✗ Firebase initialization failed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Firebase initialization error: {e}'))
