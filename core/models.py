from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import random
import string


def generate_invite_code():
    return ''.join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=6
        )
    )

def get_default_vip():
    vip, created = VipLevel.objects.get_or_create(
        level_name='VIP1'
    )
    return vip.id

class VipLevel(models.Model):
    level_name = models.CharField(max_length=20, unique=True)

    icon = models.ImageField(
        upload_to='vip_icons/',
        blank=True,
        null=True
    )

    minimum_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )

    commission_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0.0000
    )

    successive_order_commission_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0.0000
    )

    maximum_task = models.IntegerField(default=0)

    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.level_name


class UserProfile(models.Model):

    ACCOUNT_STATUS_CHOICES = [
        ('active', 'Active'),
        ('frozen', 'Frozen'),
        ('disabled', 'Disabled'),
    ]

    TRADE_STATUS_CHOICES = [
        ('enabled', 'Enabled'),
        ('disabled', 'Disabled'),
    ]

    WITHDRAWAL_STATUS_CHOICES = [
        ('enabled', 'Enabled'),
        ('disabled', 'Disabled'),
    ]

    ONLINE_STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    phone_number = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )

    frozen_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )

    gender = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    transaction_password = models.CharField(
        max_length=128,
        blank=True,
        null=True
    )

    invite_code = models.CharField(
        max_length=6,
        unique=True,
        default=generate_invite_code
    )

    invited_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='invited_users'
    )

    vip_level = models.ForeignKey(
        VipLevel,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='users',
        default=get_default_vip
    )

    credit_score = models.IntegerField(default=100)

    task_progress = models.IntegerField(default=0)

    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True
    )

    is_authorized = models.BooleanField(default=False)
    need_authorization = models.BooleanField(default=False)

    account_status = models.CharField(
        max_length=20,
        choices=ACCOUNT_STATUS_CHOICES,
        default='active'
    )

    trade_status = models.CharField(
        max_length=20,
        choices=TRADE_STATUS_CHOICES,
        default='enabled'
    )

    withdrawal_status = models.CharField(
        max_length=20,
        choices=WITHDRAWAL_STATUS_CHOICES,
        default='enabled'
    )

    online_status = models.CharField(
        max_length=20,
        choices=ONLINE_STATUS_CHOICES,
        default='offline'
    )

    recent_login = models.DateTimeField(
        blank=True,
        null=True
    )

    registration_time = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.user.username

class Product(models.Model):
    name = models.CharField(max_length=255)

    cover = models.URLField(blank=True, null=True)

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )

    score = models.IntegerField(default=0)

    description = models.TextField(blank=True, null=True)

    goods_album_1 = models.URLField(blank=True, null=True)
    goods_album_2 = models.URLField(blank=True, null=True)
    goods_album_3 = models.URLField(blank=True, null=True)
    goods_album_4 = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

def generate_product_id():
    while True:
        product_id = random.randint(10000, 99999)

        if not Product.objects.filter(product_id=product_id).exists():
            return product_id


class Product(models.Model):

    product_id = models.IntegerField(
        unique=True,
        default=generate_product_id,
        editable=False
    )

    name = models.CharField(max_length=255)

    cover = models.URLField(blank=True, null=True)

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )

    score = models.IntegerField(default=0)

    description = models.TextField(blank=True, null=True)

    goods_album_1 = models.URLField(blank=True, null=True)
    goods_album_2 = models.URLField(blank=True, null=True)
    goods_album_3 = models.URLField(blank=True, null=True)
    goods_album_4 = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ProductEvaluation(models.Model):

    star_level = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=5.0
    )

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.star_level} - {self.content[:30]}'

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
