"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from catalog.views import product_list, product_detail, add_to_cart, cart_detail, update_cart_quantity, remove_from_cart, clear_cart, checkout, payment_options, signup, favorites, add_to_favorites, remove_from_favorites, order_history, cancel_order, staff_order_dashboard, staff_product_list, staff_product_detail, staff_home, logout, home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('accounts/logout/', logout, name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/signup/', signup, name='signup'),
    path('shop/', product_list, name='product_list'), 
    
    # --- ADD THESE TWO LINES ---
    path('shop/cart/', cart_detail, name='cart_detail'),
    path('shop/cart/add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('shop/cart/update/<int:product_id>/', update_cart_quantity, name='update_cart_quantity'),
    path('shop/cart/remove/<int:product_id>/', remove_from_cart, name='remove_from_cart'),
    path('shop/cart/clear/', clear_cart, name='clear_cart'),
    path('shop/payment/', payment_options, name='payment_options'),
    path('shop/checkout/', checkout, name='checkout'),
    path('staff/', staff_home, name='staff_home'),
    path('staff/orders/', staff_order_dashboard, name='staff_order_dashboard'),
    path('staff/products/', staff_product_list, name='staff_product_list'),
    path('staff/products/<int:pk>/', staff_product_detail, name='staff_product_detail'),
    path('orders/', order_history, name='order_history'),
    path('orders/cancel/<int:order_id>/', cancel_order, name='cancel_order'),
    path('favorites/', favorites, name='favorites'),
    path('favorites/add/<int:product_id>/', add_to_favorites, name='add_to_favorites'),
    path('favorites/remove/<int:product_id>/', remove_from_favorites, name='remove_from_favorites'),
    # ---------------------------

    path('shop/<int:pk>/', product_detail, name='product_detail'),
    path('shop/<str:category_name>/', product_list, name='product_list_by_category'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)