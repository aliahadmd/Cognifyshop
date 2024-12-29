import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .webhook_handler import handle_successful_payment, handle_failed_payment

@require_POST
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)
        
    # Handle the checkout.session.completed event
    if event.type == 'checkout.session.completed':
        session = event.data.object
        return handle_successful_payment(session)
        
    # Handle the checkout.session.async_payment_failed event
    elif event.type == 'checkout.session.async_payment_failed':
        session = event.data.object
        return handle_failed_payment(session)
        
    return HttpResponse(status=200) 