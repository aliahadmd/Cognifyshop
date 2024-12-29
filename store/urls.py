from django.urls import path
from . import views, webhooks

app_name = 'store'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product-list'),
    path('category/<slug:category_slug>/', views.ProductListView.as_view(), name='category-detail'),
    path('product/<slug:product_slug>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('cart/', views.cart_detail, name='cart-detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add-to-cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove-from-cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/success/', views.order_success, name='order-success'),
    path('webhook/stripe/', webhooks.stripe_webhook, name='stripe-webhook'),
    path('orders/', views.OrderHistoryView.as_view(), name='order-history'),
    path('product/<int:product_id>/review/', views.add_review, name='add-review'),
    path('cart/count/', views.cart_count, name='cart-count'),
] 