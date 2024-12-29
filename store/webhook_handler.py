import stripe
from django.conf import settings
from django.http import HttpResponse
from .models import Order

stripe.api_key = settings.STRIPE_SECRET_KEY

def handle_successful_payment(session):
    """Handle successful payment webhook from Stripe"""
    try:
        # Get the order using the Stripe session ID
        order = Order.objects.get(stripe_id=session.id)
        
        # Update order status
        order.status = Order.COMPLETED
        order.save()
        
        return HttpResponse(status=200)
        
    except Order.DoesNotExist:
        return HttpResponse(status=404)

def handle_failed_payment(session):
    """Handle failed payment webhook from Stripe"""
    try:
        # Get the order using the Stripe session ID
        order = Order.objects.get(stripe_id=session.id)
        
        # Update order status
        order.status = Order.FAILED
        order.save()
        
        return HttpResponse(status=200)
        
    except Order.DoesNotExist:
        return HttpResponse(status=404) 