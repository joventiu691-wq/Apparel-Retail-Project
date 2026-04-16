from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Group
from .models import Product, Category, Order

STAFF_GROUP_NAME = 'Staff'


class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price', 'stock')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    ordering = ('name',)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'full_name', 'phone', 'address', 'status', 'total_price', 'order_items_summary', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('full_name', 'user__username', 'phone', 'email', 'address', 'order_items')
    readonly_fields = ('created_at', 'updated_at', 'order_items')
    actions = ['mark_as_completed']

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return self.readonly_fields
        return self.readonly_fields + ('user', 'full_name', 'email', 'phone', 'address', 'payment_method', 'total_price')

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def mark_as_completed(self, request, queryset):
        updated = queryset.filter(status=Order.STATUS_PENDING).update(status=Order.STATUS_COMPLETED)
        self.message_user(request, f"{updated} order(s) marked as completed.")
    mark_as_completed.short_description = 'Mark selected pending orders as completed'

    def order_items_summary(self, obj):
        return obj.order_items
    order_items_summary.short_description = 'Order Items'


class CustomUserAdmin(BaseUserAdmin):
    actions = ['make_staff_user', 'remove_staff_user']

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            actions.pop('make_staff_user', None)
            actions.pop('remove_staff_user', None)
        return actions

    def make_staff_user(self, request, queryset):
        staff_group, _ = Group.objects.get_or_create(name=STAFF_GROUP_NAME)
        for user in queryset:
            user.groups.add(staff_group)
            user.is_staff = True
            user.save(update_fields=['is_staff'])
        self.message_user(request, 'Selected users were converted to staff.')
    make_staff_user.short_description = 'Convert selected users to staff'

    def remove_staff_user(self, request, queryset):
        staff_group, _ = Group.objects.get_or_create(name=STAFF_GROUP_NAME)
        for user in queryset:
            user.groups.remove(staff_group)
            if not user.is_superuser and not user.groups.exists():
                user.is_staff = False
                user.save(update_fields=['is_staff'])
        self.message_user(request, 'Selected users were removed from staff.')
    remove_staff_user.short_description = 'Remove selected users from staff'


# Register your models here.

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, CustomUserAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Order, OrderAdmin)