from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Order,OrderItem
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings

def home(request):
    products = Product.objects.all()[:6]
    return render(request, 'store/home.html', {'products': products})

def products(request):
    products = Product.objects.all()
    return render(request, 'store/products.html', {'products': products})

def product_detail(request, id):
    product = Product.objects.get(id=id)
    return render(request, 'store/product_detail.html', {'product': product})

def cart(request):
    return render(request, 'store/cart.html')

def checkout(request):
    return render(request, 'store/checkout.html')

def user_register(request):
    if request.method == 'POST':
        User.objects.create_user(
            username=request.POST['username'],
            password=request.POST['password']
        )
        return redirect('login')
    return render(request, 'store/register.html')


def user_login(request):
    if request.method == 'POST':
        user = authenticate(
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user:
            login(request, user)
            return redirect('home')
    return render(request, 'store/login.html')


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        cart[str(product_id)]['quantity'] += 1
    else:
        cart[str(product_id)] = {
            'name': product.name,
            'price': float(product.price),
            'quantity': 1,
            'image': product.image.url
        }

    request.session['cart'] = cart
    return redirect('cart')


def cart(request):
    cart = request.session.get('cart', {})
    total = sum(item['price'] * item['quantity'] for item in cart.values())

    return render(request, 'store/cart.html', {
        'cart': cart,
        'total': total
    })


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        del cart[str(product_id)]

    request.session['cart'] = cart
    return redirect('cart')


@login_required(login_url='login')
def checkout(request):
    cart = request.session.get('cart', {})

    if not cart:
        return redirect('cart')

    total_price = 0

    # Calculate total price
    for product_id, item in cart.items():
        total_price += float(item['price']) * int(item['quantity'])

    # ✅ Create PAID order
    order = Order.objects.create(
        user=request.user,
        total_price=total_price,
        paid=True   # 👈 Mark as PAID
    )

    # Create order items
    for product_id, item in cart.items():
        product = Product.objects.get(id=product_id)
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=item['quantity']
        )

    # Clear cart
    request.session['cart'] = {}

    return redirect('order_success')

@login_required(login_url='login')
def order_history(request):
    orders = Order.objects.filter(
        user=request.user
    ).exclude(status='Cancelled').order_by('-created_at')

    return render(request, 'store/order_history.html', {
        'orders': orders
    })
@login_required(login_url='login')
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status == 'Processing':
        order.status = 'Cancelled'
        order.save()

        # 📧 SEND EMAIL
        subject = f"Order #{order.id} Cancelled"
        message = f"""
            Hello {order.user.username},

            Your order #{order.id} has been successfully cancelled.

            Order Details:
            • Order ID: {order.id}
            • Total Amount: ₹{order.total_price}
            • Payment Status: {"Paid" if order.paid else "Unpaid"}

            If you have already paid, the refund will be processed shortly.

            Thank you,
            Bakery Shop 🍰
            """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.user.email],
            fail_silently=False,
        )

    return redirect('order_history')

@login_required
def order_success(request):
    return render(request, 'store/order_success.html')