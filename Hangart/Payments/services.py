import requests
import uuid
import hashlib
import hmac
from django.conf import settings
from .models import PaymentTransaction, PaymentLog


class MoMoPaymentService:
    """MTN Mobile Money Payment Integration"""
    
    def __init__(self):
        self.subscription_key = getattr(settings, 'MOMO_SUBSCRIPTION_KEY', 'd57b0199d25542d896562311855d809f')
        self.api_user = getattr(settings, 'MOMO_API_USER', '')  # You'll get this after creating API user
        self.api_key = getattr(settings, 'MOMO_API_KEY', '')  # You'll get this after creating API key
        self.base_url = 'https://sandbox.momodeveloper.mtn.com'  # Use production URL in production
        self.callback_url = getattr(settings, 'MOMO_CALLBACK_URL', 'https://hangart.pythonanywhere.com/api/payments/webhook/')
        self.access_token = None
    
    def create_api_user(self, reference_id=None):
        """
        Create API User (One-time setup)
        Save the reference_id as MOMO_API_USER in settings
        """
        if not reference_id:
            reference_id = str(uuid.uuid4())
        
        url = f"{self.base_url}/v1_0/apiuser"
        headers = {
            'X-Reference-Id': reference_id,
            'Ocp-Apim-Subscription-Key': self.subscription_key,
            'Content-Type': 'application/json'
        }
        payload = {
            'providerCallbackHost': 'hangart.pythonanywhere.com'
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 201:
            print(f"✅ API User created successfully!")
            print(f"📝 Save this as MOMO_API_USER: {reference_id}")
            return {'success': True, 'api_user': reference_id}
        else:
            print(f"❌ Failed to create API User: {response.text}")
            return {'success': False, 'error': response.text}
    
    def create_api_key(self, api_user=None):
        """
        Create API Key (One-time setup)
        Save the returned key as MOMO_API_KEY in settings
        """
        if not api_user:
            api_user = self.api_user
        
        url = f"{self.base_url}/v1_0/apiuser/{api_user}/apikey"
        headers = {
            'Ocp-Apim-Subscription-Key': self.subscription_key,
        }
        
        response = requests.post(url, headers=headers)
        
        if response.status_code == 201:
            api_key = response.json()['apiKey']
            print(f"✅ API Key created successfully!")
            print(f"📝 Save this as MOMO_API_KEY: {api_key}")
            return {'success': True, 'api_key': api_key}
        else:
            print(f"❌ Failed to create API Key: {response.text}")
            return {'success': False, 'error': response.text}
    
    def get_access_token(self):
        """Generate OAuth access token"""
        url = f"{self.base_url}/collection/token/"
        headers = {
            'Ocp-Apim-Subscription-Key': self.subscription_key,
        }
        auth = (self.api_user, self.api_key)
        
        try:
            response = requests.post(url, headers=headers, auth=auth, timeout=10)
            if response.status_code == 200:
                self.access_token = response.json()['access_token']
                return self.access_token
            else:
                print(f"❌ Token error: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Token exception: {str(e)}")
            return None
    
    def request_to_pay(self, payment, phone_number=None):
        """
        Initiate payment request
        Customer will receive USSD prompt on their phone
        
        Args:
            payment: PaymentTransaction object
            phone_number: Optional phone number. If not provided, uses buyer's profile phone
        """
        if not self.api_user or not self.api_key:
            return {
                'success': False,
                'error': 'MoMo API credentials not configured. Please run setup first.'
            }
        
        if not self.access_token:
            token = self.get_access_token()
            if not token:
                return {'success': False, 'error': 'Failed to get access token'}
        
        reference_id = str(uuid.uuid4())
        url = f"{self.base_url}/collection/v1_0/requesttopay"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-Reference-Id': reference_id,
            'X-Target-Environment': 'sandbox',
            'Ocp-Apim-Subscription-Key': self.subscription_key,
            'Content-Type': 'application/json',
        }
        
        # Only add callback URL if it's configured and valid
        if self.callback_url and not self.callback_url.startswith('https://hangart.pythonanywhere.com'):
            # Don't use PythonAnywhere URL in sandbox - it triggers WAF
            pass
        # Callback is optional in sandbox, so we'll skip it
        
        # Get phone number - either from parameter or buyer profile
        if phone_number:
            phone = phone_number
        else:
            try:
                phone = payment.order.buyer.buyerprofile.phone
            except:
                return {
                    'success': False,
                    'error': 'Phone number is required. Please provide phone number in request.'
                }
        
        # Clean phone number - MoMo expects format: 25078XXXXXXX
        phone = phone.replace('+', '').replace(' ', '').replace('-', '')
        if not phone.startswith('250'):
            phone = '250' + phone.lstrip('0')
        
        # Simplified payload - avoid special characters that might trigger WAF
        # NOTE: Sandbox uses EUR, Production uses RWF
        payload = {
            'amount': str(int(payment.amount)),
            'currency': 'EUR',  # Sandbox requires EUR, change to RWF for production
            'externalId': str(payment.transaction_id),
            'payer': {
                'partyIdType': 'MSISDN',
                'partyId': phone
            },
            'payerMessage': 'Payment for HangaArt order',
            'payeeNote': 'HangaArt payment'
        }
        
        try:
            # Debug logging
            print(f"MTN Request URL: {url}")
            print(f"MTN Request Headers: {headers}")
            print(f"MTN Request Payload: {payload}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            
            # Log the response for debugging
            print(f"MTN Response Status: {response.status_code}")
            print(f"MTN Response Headers: {response.headers}")
            print(f"MTN Response Body: {response.text[:500]}")  # First 500 chars
            
            if response.status_code == 202:
                # Payment request accepted - customer will receive USSD prompt
                payment.transaction_id = reference_id
                payment.provider_response = {
                    'momo_reference': reference_id,
                    'phone': phone,
                    'status': 'pending'
                }
                payment.save()
                
                PaymentLog.objects.create(
                    payment=payment,
                    message=f"MoMo payment request sent to {phone}. Reference: {reference_id}"
                )
                
                return {
                    'success': True,
                    'reference': reference_id,
                    'phone': phone,
                    'message': 'Payment request sent. Customer will receive USSD prompt on their phone.'
                }
            else:
                error_msg = response.text
                PaymentLog.objects.create(
                    payment=payment,
                    message=f"MoMo request failed: {error_msg}"
                )
                return {'success': False, 'error': error_msg}
        
        except Exception as e:
            PaymentLog.objects.create(
                payment=payment,
                message=f"MoMo exception: {str(e)}"
            )
            return {'success': False, 'error': str(e)}
    
    def check_payment_status(self, reference_id):
        """
        Check status of payment request
        Returns: PENDING, SUCCESSFUL, or FAILED
        """
        if not self.access_token:
            self.get_access_token()
        
        url = f"{self.base_url}/collection/v1_0/requesttopay/{reference_id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-Target-Environment': 'sandbox',
            'Ocp-Apim-Subscription-Key': self.subscription_key,
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                
                return {
                    'success': True,
                    'status': status,
                    'data': data
                }
            else:
                return {
                    'success': False,
                    'error': response.text
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_payment_from_status_check(self, payment):
        """
        Check payment status and update database
        """
        result = self.check_payment_status(payment.transaction_id)
        
        if not result.get('success'):
            return result
        
        status = result.get('status')
        data = result.get('data')
        
        if status == 'SUCCESSFUL':
            payment.status = 'successful'
            payment.provider_response = data
            payment.save()
            
            # Update order
            order = payment.order
            order.status = 'paid'
            order.payment_reference = payment.transaction_id
            order.save()
            
            # Mark artworks as sold
            for item in order.items.all():
                artwork = item.artwork
                artwork.is_available = False
                artwork.status = 'sold'
                artwork.save()
            
            PaymentLog.objects.create(
                payment=payment,
                message=f"Payment successful via MoMo"
            )
            
            return {'success': True, 'status': 'successful'}
        
        elif status == 'FAILED':
            payment.status = 'failed'
            payment.provider_response = data
            payment.save()
            
            reason = data.get('reason', 'Unknown error')
            PaymentLog.objects.create(
                payment=payment,
                message=f"Payment failed: {reason}"
            )
            
            return {'success': True, 'status': 'failed', 'reason': reason}
        
        else:  # PENDING
            PaymentLog.objects.create(
                payment=payment,
                message=f"Payment still pending"
            )
            return {'success': True, 'status': 'pending'}


# For future use - Flutterwave integration
class FlutterwavePaymentService:
    """Flutterwave Payment Integration (Cards, Mobile Money, Bank)"""
    
    def __init__(self):
        self.base_url = 'https://api.flutterwave.com/v3'
        self.secret_key = getattr(settings, 'FLW_SECRET_KEY', '')
        self.public_key = getattr(settings, 'FLW_PUBLIC_KEY', '')
    
    def initialize_payment(self, payment):
        """Initialize Flutterwave payment - to be implemented"""
        return {'success': False, 'error': 'Flutterwave not yet configured'}
