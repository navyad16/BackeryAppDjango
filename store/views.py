from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Order, OrderItem,ProductFeedback
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.db.models import Q
from django.contrib import messages


# ================= HOME & PRODUCTS =================

def home(request):
    query = request.GET.get('q', '')

    products = Product.objects.all()

    if query :
        products = products.filter(name__icontains=query)

    return render(request, 'store/home.html', {
        'products': products,
        'query': query
    })

def products(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', 'all')

    products = Product.objects.all()

    if query.strip():   # 👈 important
        products = products.filter(name__icontains=query)

    if category != 'all':
        products = products.filter(category__name__iexact=category)

    categories = ['Cake', 'Cookies', 'Bread']

    return render(request, 'store/products.html', {
        'products': products,
        'query': query,
        'category': category,
        'categories': categories
    })
def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    feedbacks = ProductFeedback.objects.filter(product=product).order_by("-created_at")

    has_purchased = False
    if request.user.is_authenticated:
        has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            product=product,
            order__paid=True
        ).exists()

    if request.method == "POST" and has_purchased:
        rating = request.POST.get("rating")
        comment = request.POST.get("comment")

        ProductFeedback.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            comment=comment
        )

        return redirect("product_detail", id=product.id)

    return render(request, "store/product_detail.html", {
        "product": product,
        "feedbacks": feedbacks,
        "has_purchased": has_purchased
    })


# ================= AUTH =================

def user_register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get('email')  
        password = request.POST.get("password")

        # ✅ Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please choose another.")
            return redirect("register")
        
        # ❌ Check duplicate email
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return redirect('register')

        # ✅ Create user
        User.objects.create_user(
            username=username,
            password=password,
            email=email
        )

        messages.success(request, "Account created successfully. Please login.")
        return redirect("login")

    return render(request, "store/register.html")

def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)   # ✅ THIS SAVES SESSION
            return redirect("home")
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "store/login.html")


# ================= CART =================

def cart(request):
    cart = request.session.get('cart', {})
    total = sum(
        float(item['price']) * int(item['quantity'])
        for item in cart.values()
    )
    return render(request, 'store/cart.html', {
        'cart': cart,
        'total': total
    })


# 🔥 UPDATED ADD TO CART (WITH QUANTITY FROM PRODUCT PAGE)
@login_required(login_url='login')
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    quantity = int(request.POST.get('quantity', 1))  # 👈 from + / − buttons
    product_id = str(product_id)

    cart = request.session.get('cart', {})

    if product_id in cart:
        cart[product_id]['quantity'] += quantity
    else:
        cart[product_id] = {
            'name': product.name,
            'price': float(product.price),
            'quantity': quantity,
            'image': product.image.url
        }

    request.session['cart'] = cart
    return redirect('cart')


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_id = str(product_id)

    if product_id in cart:
        del cart[product_id]

    request.session['cart'] = cart
    return redirect('cart')


# ================= AJAX QUANTITY UPDATE =================

def update_cart_quantity(request):
    if request.method == "POST":
        product_id = str(request.POST.get("product_id"))
        action = request.POST.get("action")

        cart = request.session.get("cart", {})

        if product_id in cart:
            if action == "increase":
                cart[product_id]["quantity"] += 1
            elif action == "decrease" and cart[product_id]["quantity"] > 1:
                cart[product_id]["quantity"] -= 1

        request.session["cart"] = cart

        item = cart[product_id]
        item_total = float(item["price"]) * item["quantity"]
        grand_total = sum(
            float(i["price"]) * i["quantity"] for i in cart.values()
        )

        return JsonResponse({
            "quantity": item["quantity"],
            "item_total": round(item_total, 2),
            "grand_total": round(grand_total, 2)
        })


# ================= CHECKOUT & ORDERS =================

@login_required(login_url='login')
def checkout(request):
    cart = request.session.get('cart', {})

    if not cart:
        return redirect('cart')

    total_price = sum(
        float(item['price']) * int(item['quantity'])
        for item in cart.values()
    )

    order = Order.objects.create(
        user=request.user,
        total_price=total_price,
        paid=True
    )

    for product_id, item in cart.items():
        product = Product.objects.get(id=product_id)
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=item['quantity']
        )

    request.session['cart'] = {}
    return redirect('order_success')


@login_required
def order_success(request):
    return render(request, 'store/order_success.html')


@login_required
def order_history(request):
    orders = Order.objects.filter(
        user=request.user
    ).exclude(status='Cancelled').order_by('-created_at')

    return render(request, 'store/order_history.html', {'orders': orders})


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status != 'Cancelled':
        order.status = 'Cancelled'
        order.save()

        # ✅ SEND EMAIL
        send_mail(
            subject='Your Order Has Been Cancelled',
            message=f'''
            Hello {request.user.username},

            Your order (ID: {order.id}) has been cancelled successfully.

            Order Amount: ₹{order.total_price}

            If this was not you, please contact support.

            Thank you,
            Bakery Shop 🍰
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            fail_silently=False,
        )

        messages.success(request, 'Order cancelled and email sent')

    return redirect('order_history')

def logout_view(request):
    logout(request)
    return redirect("home")