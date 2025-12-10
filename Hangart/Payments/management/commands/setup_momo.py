from django.core.management.base import BaseCommand
from Payments.services import MoMoPaymentService
import uuid


class Command(BaseCommand):
    help = 'Set up MTN Mobile Money API credentials (one-time setup)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 MTN Mobile Money Setup'))
        self.stdout.write('=' * 60)
        
        service = MoMoPaymentService()
        
        # Check if already configured
        if service.api_user and service.api_key:
            self.stdout.write(self.style.WARNING('⚠️  MoMo is already configured!'))
            self.stdout.write(f'API User: {service.api_user}')
            self.stdout.write(f'API Key: {service.api_key[:8]}...')
            
            response = input('\nDo you want to create new credentials? (yes/no): ')
            if response.lower() != 'yes':
                return
        
        self.stdout.write('\n📝 Step 1: Creating API User...')
        
        # Generate a new UUID for API user
        api_user_id = str(uuid.uuid4())
        
        result = service.create_api_user(api_user_id)
        
        if result.get('success'):
            self.stdout.write(self.style.SUCCESS(f'✅ API User created: {api_user_id}'))
            
            self.stdout.write('\n📝 Step 2: Creating API Key...')
            
            # Wait a moment for API user to be ready
            import time
            time.sleep(2)
            
            key_result = service.create_api_key(api_user_id)
            
            if key_result.get('success'):
                api_key = key_result['api_key']
                self.stdout.write(self.style.SUCCESS(f'✅ API Key created: {api_key}'))
                
                self.stdout.write('\n' + '=' * 60)
                self.stdout.write(self.style.SUCCESS('✅ Setup Complete!'))
                self.stdout.write('=' * 60)
                self.stdout.write('\n📋 Add these to your settings.py:')
                self.stdout.write(f"\nMOMO_API_USER = '{api_user_id}'")
                self.stdout.write(f"MOMO_API_KEY = '{api_key}'")
                self.stdout.write('\n' + '=' * 60)
                
                # Offer to update settings automatically
                response = input('\n❓ Do you want to update settings.py automatically? (yes/no): ')
                if response.lower() == 'yes':
                    self.update_settings(api_user_id, api_key)
            else:
                self.stdout.write(self.style.ERROR(f'❌ Failed to create API Key'))
                self.stdout.write(self.style.ERROR(key_result.get('error', 'Unknown error')))
        else:
            self.stdout.write(self.style.ERROR('❌ Failed to create API User'))
            self.stdout.write(self.style.ERROR(result.get('error', 'Unknown error')))
    
    def update_settings(self, api_user, api_key):
        """Update settings.py with the new credentials"""
        import os
        from django.conf import settings
        
        settings_path = os.path.join(settings.BASE_DIR, 'Hangart', 'settings.py')
        
        try:
            with open(settings_path, 'r') as f:
                content = f.read()
            
            # Update MOMO_API_USER
            if "MOMO_API_USER = ''" in content:
                content = content.replace(
                    "MOMO_API_USER = ''",
                    f"MOMO_API_USER = '{api_user}'"
                )
            
            # Update MOMO_API_KEY
            if "MOMO_API_KEY = ''" in content:
                content = content.replace(
                    "MOMO_API_KEY = ''",
                    f"MOMO_API_KEY = '{api_key}'"
                )
            
            with open(settings_path, 'w') as f:
                f.write(content)
            
            self.stdout.write(self.style.SUCCESS('\n✅ settings.py updated successfully!'))
            self.stdout.write(self.style.WARNING('⚠️  Please restart your Django server for changes to take effect.'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Failed to update settings.py: {str(e)}'))
            self.stdout.write(self.style.WARNING('Please update manually.'))
