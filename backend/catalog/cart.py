from .models import Product

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, product_id, quantity=1):
        p_id = str(product_id)
        if p_id not in self.cart:
            self.cart[p_id] = {'quantity': 0}
        self.cart[p_id]['quantity'] += int(quantity)
        self.session.modified = True

    def decrement(self, product_id, quantity=1):
        p_id = str(product_id)
        if p_id in self.cart:
            self.cart[p_id]['quantity'] -= int(quantity)
            if self.cart[p_id]['quantity'] <= 0:
                del self.cart[p_id]
            self.session.modified = True

    def set_quantity(self, product_id, quantity):
        p_id = str(product_id)
        if int(quantity) <= 0:
            self.remove(product_id)
        else:
            self.cart[p_id] = {'quantity': int(quantity)}
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
            self.session.modified = True