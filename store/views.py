from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.conf import settings
from .models import Category, Product, Cart, CartItem, Order, OrderItem
import stripe
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .forms import ReviewForm
from django.urls import reverse

stripe.api_key = settings.STRIPE_SECRET_KEY

class ProductListView(ListView):
    model = Product
    context_object_name = 'products'
    template_name = 'store/product_list.html'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(available=True)
        
        # Handle category filter
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            queryset = queryset.filter(category=category)
        
        # Handle search query
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['search_query'] = self.request.GET.get('q', '')
        return context

class ProductDetailView(DetailView):
    model = Product
    context_object_name = 'product'
    template_name = 'store/product_detail.html'
    slug_url_kwarg = 'product_slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['review_form'] = ReviewForm()
        return context

@login_required
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f'{product.name} added to cart.')
    response = HttpResponse(status=204)
    response['HX-Trigger'] = 'cartUpdated'
    return response

@login_required
@require_POST
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, 'Item removed from cart.')
    response = HttpResponse(status=204)
    response['HX-Trigger'] = 'cartUpdated'
    return response

@login_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'store/cart_detail.html', {'cart': cart})

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    if request.method == 'POST':
        try:
            # Create Stripe checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': int(item.product.price * 100),  # Convert to cents
                        'product_data': {
                            'name': item.product.name,
                            'description': item.product.description[:255],  # Stripe has a limit
                            'images': [request.build_absolute_uri(item.product.image.url)] if item.product.image else [],
                        },
                    },
                    'quantity': item.quantity,
                } for item in cart.items.all()],
                mode='payment',
                success_url=request.build_absolute_uri(reverse('store:order-success')),
                cancel_url=request.build_absolute_uri(reverse('store:cart-detail')),
                metadata={
                    'user_id': request.user.id,
                }
            )
            
            # Create order
            order = Order.objects.create(
                user=request.user,
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                email=request.POST['email'],
                address=request.POST['address'],
                postal_code=request.POST['postal_code'],
                city=request.POST['city'],
                stripe_id=checkout_session.id
            )
            
            # Create order items
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity
                )
            
            # Clear the cart
            cart.items.all().delete()
            
            return redirect(checkout_session.url)
            
        except Exception as e:
            messages.error(request, f'There was an error processing your payment: {str(e)}')
            return redirect('store:cart-detail')
            
    return render(request, 'store/checkout.html', {
        'cart': cart,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY
    })

@login_required
def order_success(request):
    return render(request, 'store/order_success.html')

class OrderHistoryView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'store/order_history.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created')

@login_required
@require_POST
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    form = ReviewForm(request.POST)
    
    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.user = request.user
        try:
            review.save()
            messages.success(request, 'Review added successfully.')
        except IntegrityError:
            messages.error(request, 'You have already reviewed this product.')
    else:
        messages.error(request, 'Error adding review.')
    
    return redirect(product.get_absolute_url())

@login_required
def cart_count(request):
    cart = Cart.objects.get(user=request.user)
    return HttpResponse(f'<span class="badge bg-primary">{cart.items.count()}</span>')
