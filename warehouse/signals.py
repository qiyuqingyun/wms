from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver

from .models import BatchLocation, Item, ItemBatch, Location, Movement


@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    if sender.name != 'warehouse':
        return
    managers, _ = Group.objects.get_or_create(name='Managers')
    operators, _ = Group.objects.get_or_create(name='Operators')

    # Managers: all permissions on warehouse models
    for model in (Item, ItemBatch, Location, Movement, BatchLocation):
        ct = ContentType.objects.get_for_model(model)
        perms = Permission.objects.filter(content_type=ct)
        managers.permissions.add(*perms)

    # Operators: view + add movement + 编辑包装（change item）
    for model in (Item, ItemBatch, Location, BatchLocation):
        ct = ContentType.objects.get_for_model(model)
        view_perm = Permission.objects.get(content_type=ct, codename=f'view_{model._meta.model_name}')
        operators.permissions.add(view_perm)
        if model is Item:
            change_perm = Permission.objects.get(content_type=ct, codename=f'change_{model._meta.model_name}')
            operators.permissions.add(change_perm)

    mv_ct = ContentType.objects.get_for_model(Movement)
    add_mv = Permission.objects.get(content_type=mv_ct, codename='add_movement')
    view_mv = Permission.objects.get(content_type=mv_ct, codename='view_movement')
    operators.permissions.add(add_mv, view_mv)


