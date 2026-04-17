from functools import wraps

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from .models import Product, Category, Favorite, Order, OrderItem
from .forms import ProductStaffForm
from .cart import Cart
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect

STAFF_GROUP_NAME = 'Staff'

def logout(request):
    auth_logout(request)
    return redirect('home')

def home(request):
    return render(request, 'catalog/home.html')

def product_list(request, category_name=None):
    if request.user.is_authenticated and is_staff_user(request.user):
        return redirect('staff_product_list')

    products = Product.objects.all()
    selected_category = ''
    user_favorites = []

    # If a category name is in the URL, filter the list
    if category_name:
        category = get_object_or_404(Category, name__iexact=category_name)
        products = products.filter(category=category)
        selected_category = category.name

    if request.user.is_authenticated:
        user_favorites = Favorite.objects.filter(user=request.user).values_list('product', flat=True)

    return render(request, 'catalog/product_list.html', {
        'products': products,
        'selected_category': selected_category,
        'user_favorites': user_favorites,
    })

def product_detail(request, pk):
    if request.user.is_authenticated and is_staff_user(request.user):
        return redirect('staff_product_detail', pk=pk)

    product = get_object_or_404(Product, pk=pk)
    user_favorites = []
    if request.user.is_authenticated:
        user_favorites = Favorite.objects.filter(user=request.user).values_list('product', flat=True)
    return render(request, 'catalog/product_detail.html', {'product': product, 'user_favorites': user_favorites})

def add_to_cart(request, product_id):
    cart = Cart(request)
    quantity = 1
    if request.method == 'POST':
        try:
            quantity = max(1, int(request.POST.get('quantity', 1)))
        except (TypeError, ValueError):
            quantity = 1
    else:
        try:
            quantity = max(1, int(request.GET.get('quantity', 1)))
        except (TypeError, ValueError):
            quantity = 1

    cart.add(product_id=product_id, quantity=quantity)
    return redirect('cart_detail')

@login_required
def cart_detail(request):
    cart = Cart(request)
    return render(request, 'catalog/cart_detail.html', {
        'cart': cart,
        'cart_count': cart.get_total_items(),
    })


def update_cart_quantity(request, product_id):
    cart = Cart(request)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'dec':
            cart.decrement(product_id, quantity=1)
        elif action == 'inc':
            cart.add(product_id=product_id, quantity=1)
    return redirect('cart_detail')


def remove_from_cart(request, product_id):
    cart = Cart(request)
    cart.remove(product_id)
    return redirect('cart_detail')

def clear_cart(request):
    cart = Cart(request)
    cart.clear()
    return redirect('cart_detail')

@login_required
def checkout(request):
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'unknown')
        customer_name = request.POST.get('customer_name', '')
        customer_email = request.POST.get('customer_email', '')
        customer_phone = request.POST.get('customer_phone', '')
        customer_address = request.POST.get('customer_address', '')
        cart = Cart(request)

        if cart.get_total_items() == 0:
            return redirect('cart_detail')

        ordered_items = []
        for item in cart:
            product = item['product']
            if product.stock < item['quantity']:
                return redirect('cart_detail')
            ordered_items.append(f"{item['quantity']} x {product.name}")

        order = Order.objects.create(
            user=request.user,
            full_name=customer_name,
            email=customer_email,
            phone=customer_phone,
            address=customer_address,
            payment_method=payment_method,
            total_price=cart.get_total_price(),
            order_items='; '.join(ordered_items),
            status=Order.STATUS_PENDING,
        )

        for item in cart:
            product = item['product']
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item['quantity'],
                price=product.price,
            )

        cart.clear()
        return render(request, 'catalog/checkout_success.html', {
            'payment_method': payment_method,
            'customer_name': customer_name,
            'customer_email': customer_email,
            'customer_phone': customer_phone,
            'customer_address': customer_address,
        })
    return redirect('cart_detail')

@login_required
def payment_options(request):
    cart = Cart(request)
    if cart.get_total_items() == 0:
        return redirect('cart_detail')
    return render(request, 'catalog/payment_options.html', {'cart': cart})

@csrf_protect
def signup(request):
    form = UserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('product_list')
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def favorites(request):
    favorites = Favorite.objects.filter(user=request.user)
    return render(request, 'catalog/favorites.html', {'favorites': favorites})

@login_required
def add_to_favorites(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    Favorite.objects.get_or_create(user=request.user, product=product)
    return redirect('product_detail', pk=product_id)

@login_required
def remove_from_favorites(request, product_id):
    Favorite.objects.filter(user=request.user, product_id=product_id).delete()
    return redirect('favorites')

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'catalog/order_history.html', {
        'orders': orders,
    })

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    if request.method == 'POST' and order.status == Order.STATUS_PENDING:
        order.status = Order.STATUS_CANCELLED
        order.save(update_fields=['status'])
    return redirect('order_history')


def is_staff_user(user):
    return user.is_staff or user.groups.filter(name=STAFF_GROUP_NAME).exists()


def staff_user_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if is_staff_user(request.user):
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden('You do not have permission to access this page.')
    return _wrapped


@staff_user_required
def staff_product_list(request):
    products = Product.objects.all().order_by('name')
    return render(request, 'catalog/staff_product_list.html', {
        'products': products,
    })


@staff_user_required
def staff_product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    status_message = None

    if request.method == 'POST':
        form = ProductStaffForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            status_message = 'Product details updated successfully.'
    else:
        form = ProductStaffForm(instance=product)

    return render(request, 'catalog/staff_product_detail.html', {
        'product': product,
        'form': form,
        'status_message': status_message,
    })


@staff_user_required
def staff_order_dashboard(request):
    status_message = None
    if request.method == 'POST':
        if request.POST.get('action') == 'complete_all':
            pending_orders = Order.objects.filter(status=Order.STATUS_PENDING).prefetch_related('items__product')
            completed = 0
            skipped = 0
            for order in pending_orders:
                if order.complete():
                    completed += 1
                else:
                    skipped += 1
            status_message = f'{completed} pending order(s) completed.'
            if skipped:
                status_message += f' {skipped} order(s) skipped due to insufficient stock.'

        order_id = request.POST.get('order_id')
        if order_id:
            order = get_object_or_404(Order, pk=order_id)
            if order.status == Order.STATUS_PENDING:
                if order.complete():
                    status_message = f'Order #{order.id} marked as completed.'
                else:
                    status_message = f'Order #{order.id} could not be completed because stock is unavailable.'

    orders = Order.objects.select_related('user').all()
    return render(request, 'catalog/staff_order_dashboard.html', {
        'orders': orders,
        'status_message': status_message,
    })


@staff_user_required
def staff_home(request):
    """Simple staff landing page with quick links and counts."""
    product_count = Product.objects.count()
    pending_orders_count = Order.objects.filter(status=Order.STATUS_PENDING).count()
    return render(request, 'catalog/staff_home.html', {
        'product_count': product_count,
        'pending_orders_count': pending_orders_count,
    })