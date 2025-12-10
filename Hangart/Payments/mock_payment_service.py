"""
Mock Payment Service for Testing
Use this while waiting for MTN MoMo activation
"""
import uuid
import time
from .models import PaymentTransaction, PaymentLog


class MockMoMoPaymentService:
    """
    Mock Mobile Money service for testing without real MoMo API
    Simulates payment flow for development
    """
    
    def __init__(self):
        self.mock_mode = True
    
    def request_to_pay(self, payment, phone_number=None):
        """
        Simulate payment request
        Automatically marks payment as successful after 5 seconds
        
        Args:
            payment: PaymentTransaction object
            phone_number: Optional phone number. If not provided, uses buyer's profile phone or mock
        """
        reference_id = str(uuid.uuid4())
        
        # Get phone number - either from parameter, buyer profile, or use mock
        if phone_number:
            phone = phone_number
        else:
            try:
                phone = payment.order.buyer.buyerprofile.phone
            except:
                phone = '250788000000'  # Mock phone
        
        # Clean phone number
        phone = phone.replace('+', '').replace(' ', '').replace('-', '')
        if not phone.startswith('250'):
            phone = '250' + phone.lstrip('0')
        
        # Update payment
        payment.transaction_id = reference_id
        payment.provider_response = {
            'momo_reference': reference_id,
            'phone': phone,
            'status': 'pending',
            'mock': True,
            'message': 'MOCK PAYMENT - Auto-approves in 5 seconds'
        }
        payment.save()
        
        PaymentLog.objects.create(
            payment=payment,
            message=f"[MOCK] Payment request sent to {phone}. Reference: {reference_id}"
        )
        
        # Schedule auto-approval (in real implementation, this comes from webhook)
        # For now, just return success and let frontend poll
        
        return {
            'success': True,
            'reference': reference_id,
            'phone': phone,
            'message': 'MOCK: Payment request sent. Will auto-approve in 5 seconds.',
            'mock': True
        }
    
    def check_payment_status(self, reference_id):
        """
        Simulate status check
        Automatically approves payment if pending for > 5 seconds
        """
        try:
            payment = PaymentTransaction.objects.get(transaction_id=reference_id)
            
            # If pending and created more than 5 seconds ago, mark as successful
            if payment.status == 'pending':
                time_elapsed = (payment.updated_at - payment.created_at).total_seconds()
                
                if time_elapsed > 5:
                    # Auto-approve
                    return {
                        'success': True,
                        'status': 'SUCCESSFUL',
                        'data': {
                            'status': 'SUCCESSFUL',
                            'amount': str(payment.amount),
                            'currency': 'RWF',
                            'financialTransactionId': f'MOCK-{reference_id[:8]}',
                            'externalId': payment.transaction_id,
                            'payer': {
                                'partyIdType': 'MSISDN',
                                'partyId': '250788000000'
                            },
                            'mock': True
                        }
                    }
                else:
                    # Still pending
                    return {
                        'success': True,
                        'status': 'PENDING',
                        'data': {
                            'status': 'PENDING',
                            'mock': True,
                            'seconds_remaining': int(5 - time_elapsed)
                        }
                    }
            else:
                # Already processed
                return {
                    'success': True,
                    'status': payment.status.upper(),
                    'data': payment.provider_response
                }
        
        except PaymentTransaction.DoesNotExist:
            return {
                'success': False,
                'error': 'Payment not found'
            }
    
    def update_payment_from_status_check(self, payment):
        """
        Check status and update payment
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
                message=f"[MOCK] Payment successful"
            )
            
            return {'success': True, 'status': 'successful'}
        
        elif status == 'FAILED':
            payment.status = 'failed'
            payment.provider_response = data
            payment.save()
            
            PaymentLog.objects.create(
                payment=payment,
                message=f"[MOCK] Payment failed"
            )
            
            return {'success': True, 'status': 'failed'}
        
        else:  # PENDING
            seconds = data.get('seconds_remaining', 0)
            PaymentLog.objects.create(
                payment=payment,
                message=f"[MOCK] Payment pending ({seconds}s remaining)"
            )
            return {'success': True, 'status': 'pending'}
