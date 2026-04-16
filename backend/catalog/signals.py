from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate
from django.dispatch import receiver

STAFF_GROUP_NAME = 'Staff'

@receiver(post_migrate)
def create_staff_group(sender, **kwargs):
    if sender.name != 'catalog':
        return

    staff_group, _ = Group.objects.get_or_create(name=STAFF_GROUP_NAME)
    permissions = Permission.objects.filter(
        content_type__app_label='catalog',
        codename__in=[
            'add_product',
            'change_product',
            'delete_product',
            'view_product',
            'add_category',
            'change_category',
            'view_category',
            'change_order',
            'view_order',
        ],
    )
    staff_group.permissions.set(permissions)
