from .models import Product, CartItem

class Cart:
    def __init__(self, request):
        self.session = request.session
        self.user = getattr(request, 'user', None)
        cart = self.session.get('cart', {})
        if self.user and self.user.is_authenticated:
            self.cart = self._load_authenticated_cart(cart)
        else:
            self.cart = cart
            if not self.cart:
                self.cart = self.session['cart'] = {}

    def _load_authenticated_cart(self, session_cart):
        saved_items = CartItem.objects.filter(user=self.user)
        saved_cart = {str(item.product_id): {'quantity': item.quantity} for item in saved_items}

        if session_cart and not self.session.get('cart_merged'):
            merged_cart = saved_cart.copy()
            for p_id, item in session_cart.items():
                merged_cart[p_id] = {
                    'quantity': merged_cart.get(p_id, {'quantity': 0})['quantity'] + item.get('quantity', 0)
                }
            self.session['cart'] = merged_cart
            self.cart = merged_cart
            self._save_cart_to_db()
        else:
            self.cart = saved_cart
            self.session['cart'] = self.cart

        self.session['cart_merged'] = True
        self.session.modified = True
        return self.cart

    def _save_cart_to_db(self):
        if not self.user or not self.user.is_authenticated:
            return

        CartItem.objects.filter(user=self.user).delete()
        cart_items = []
        for p_id, item in self.cart.items():
            quantity = int(item.get('quantity', 0))
            if quantity <= 0:
                continue
            cart_items.append(CartItem(user=self.user, product_id=int(p_id), quantity=quantity))
        if cart_items:
            CartItem.objects.bulk_create(cart_items)

    def add(self, product_id, quantity=1):
        p_id = str(product_id)
        if p_id not in self.cart:
            self.cart[p_id] = {'quantity': 0}
        self.cart[p_id]['quantity'] += int(quantity)
        self.session['cart'] = self.cart
        if self.user and self.user.is_authenticated:
            self._save_cart_to_db()
        self.session.modified = True

    def decrement(self, product_id, quantity=1):
        p_id = str(product_id)
        if p_id in self.cart:
            self.cart[p_id]['quantity'] -= int(quantity)
            if self.cart[p_id]['quantity'] <= 0:
                del self.cart[p_id]
            self.session['cart'] = self.cart
            if self.user and self.user.is_authenticated:
                self._save_cart_to_db()
            self.session.modified = True

    def set_quantity(self, product_id, quantity):
        p_id = str(product_id)
        if int(quantity) <= 0:
            self.remove(product_id)
        else:
            self.cart[p_id] = {'quantity': int(quantity)}
            self.session['cart'] = self.cart
            if self.user and self.user.is_authenticated:
                self._save_cart_to_db()
            self.session.modified = True

    def get_total_items(self):
        return sum(item['quantity'] for item in self.cart.values())

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        for product in products:
            self.cart[str(product.id)]['product'] = product
        for item in self.cart.values():
            item['total_price'] = item['product'].price * item['quantity']
            yield item

    def get_total_price(self):
        return sum(item['product'].price * item['quantity'] for item in self)

    def remove(self, product_id):
        p_id = str(product_id)
        if p_id in self.cart:
            del self.cart[p_id]
            self.session['cart'] = self.cart
            if self.user and self.user.is_authenticated:
                CartItem.objects.filter(user=self.user, product_id=int(p_id)).delete()
            self.session.modified = True

    def clear(self):
        self.cart.clear()
        self.session['cart'] = self.cart
        if self.user and self.user.is_authenticated:
            CartItem.objects.filter(user=self.user).delete()
        self.session.modified = True