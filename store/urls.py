from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.products, name='products'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),

    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('cart/update/', views.update_cart_quantity, name='update_cart_quantity'),

    path('remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),

    path('checkout/', views.checkout, name='checkout'),
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path("logout/", views.logout_view, name="logout"),
    path('my-orders/', views.order_history, name='order_history'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('order-success/', views.order_success, name='order_success'),
]
