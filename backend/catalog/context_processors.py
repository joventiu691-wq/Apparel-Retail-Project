def extras(request):
    from catalog.models import Category
    from catalog.cart import Cart
    cart = Cart(request)
    return {
        'all_categories': Category.objects.all(),
        'cart_count': cart.get_total_items()
    }