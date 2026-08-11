from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

import random
import string


def generate_invite_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def generate_withdrawal_id():
    now = timezone.now()
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"WD{now.strftime('%Y%m%d%H%M%S')}{random_part}"


def generate_deposit_id():
    now = timezone.now()
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"DP{now.strftime('%Y%m%d%H%M%S')}{random_part}"


def generate_product_id():
    while True:
        product_id = random.randint(10000, 99999)

        if not Product.objects.filter(product_id=product_id).exists():
            return product_id

class HomePageSettings(models.Model):
    BANNER_TYPE_CHOICES = [
        ("image", "Image"),
        ("video", "Video"),
    ]

    brand_name = models.CharField(
        max_length=100,
        default="LANDOR",
    )

    announcement = models.TextField(
        default="Welcome to our platform",
    )

    banner_type = models.CharField(
        max_length=10,
        choices=BANNER_TYPE_CHOICES,
        default="image",
    )

    banner_url = models.URLField(
        max_length=1000,
        blank=True,
    )

    online_users_value = models.CharField(
        max_length=30,
        default="3.015k",
    )

    online_users_note = models.CharField(
        max_length=100,
        default="+ 29% From Last Month",
    )

    order_completion_value = models.CharField(
        max_length=30,
        default="5.016k",
    )

    order_completion_note = models.CharField(
        max_length=100,
        default="171% ↑",
    )

    optimize_demand_value = models.CharField(
        max_length=30,
        default="305k",
    )

    optimize_demand_note = models.CharField(
        max_length=100,
        default="+ 160% From Last Month",
    )

    order_quantity_value = models.CharField(
        max_length=30,
        default="5.164k",
    )

    order_quantity_note = models.CharField(
        max_length=100,
        default="157% ↑",
    )

    order_banner_url = models.URLField(
        max_length=1000,
        blank=True,
        default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775243934/download_3_gu3ks5.png",
    )
    order_banner_type = models.CharField(
        max_length=10,
        choices=BANNER_TYPE_CHOICES,
        default="image",
    )
    order_description_html = models.TextField(
        default=(
            "<h2>Order Description</h2>"
            "<p>Order instructions and information will be published here.</p>"
        )
    )
    please_note_html = models.TextField(
        default=(
            "<h2>Please Note</h2>"
            "<p>Important order notices will be published here.</p>"
        )
    )

    terms_and_conditions_html = models.TextField(
        default=(
            "<h2>User Registration Agreement</h2>"
            "<p>Welcome to Landor.</p>"
            "<p>Please read these Terms and Conditions carefully before using "
            "this website. By registering or continuing to use the platform, "
            "you confirm that you understand and accept these terms.</p>"
            "<h3>1. User information</h3>"
            "<p>You agree to provide accurate registration information and to "
            "keep your account credentials secure.</p>"
            "<h3>2. Platform use</h3>"
            "<p>You agree to use the platform lawfully and in accordance with "
            "the rules shown on this page.</p>"
        )
    )

    transaction_notice_html = models.TextField(
        default=(
            "<h2>Transaction Notice</h2>"
            "<p>Important transaction announcements will be published here.</p>"
        )
    )
    campaign_html = models.TextField(
        default=(
            "<h2>Campaign</h2>"
            "<p>Current campaign information will be published here.</p>"
        )
    )
    illustrate_html = models.TextField(
        default=(
            "<h2>Illustrate</h2>"
            "<p>Platform instructions and illustrations will be published here.</p>"
        )
    )
    faqs_html = models.TextField(
        default=(
            "<h2>Frequently Asked Questions</h2>"
            "<h3>How do I use the platform?</h3>"
            "<p>Please follow the instructions shown on each page.</p>"
        )
    )
    company_profile_html = models.TextField(
        default=(
            "<h2>Company Profile</h2>"
            "<p>Company information will be published here.</p>"
        )
    )

    withdrawal_icon_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775312902/download_4_ijox13.png")
    deposit_icon_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775312902/download_5_flfcf2.png")
    customer_service_icon_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775312901/download_6_x6blhw.png")
    online_customer_service_icon_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775243935/download_2_fjlpca.png")
    transaction_notice_icon_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775312901/download_7_exqqzc.png")
    campaign_icon_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775312901/download_8_uczm9q.png")
    illustrate_icon_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775312901/download_9_yfakmr.png")
    faqs_icon_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775312901/download_10_laivzw.png")
    company_profile_icon_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775312901/download_11_nepxza.png")

    home_nav_active_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775243935/download_o2t6x5.png")
    home_nav_inactive_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775243799/ohome.0cf9ec80_edaksd.png")
    records_nav_active_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775243935/download_1_gzqqjd.png")
    records_nav_inactive_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775243799/orecords.44d9036b_pjxc8m.png")
    order_nav_active_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775243799/startingActive3.f51cf26f_dnesyh.png")
    order_nav_inactive_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775245492/ostarting.8b1ceecf_ko8hha.png")
    messages_nav_active_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775243935/download_2_fjlpca.png")
    messages_nav_inactive_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775243799/omessages.7280e6e4_ht6fcx.png")
    settings_nav_active_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775243934/download_3_gu3ks5.png")
    settings_nav_inactive_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775243799/oprofile.e21aa036_bkgray.png")

    default_profile_icon_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1778628056/profile_h2zimj.png")
    order_description_icon_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1778637234/order_description_wf0ij5.png")
    please_note_icon_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1778637234/note_vmbnnb.png")
    wallet_icon_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1778880278/Wallet_evtebh.png")
    settings_deposit_icon_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1778628584/card-sendOrange1.f6dd01ed_y9vcf7.png")
    settings_withdraw_icon_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1778628585/withdraw_rrfcwq.png")
    trading_account_icon_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1778628585/trading_account_lbpikk.png")
    personal_information_icon_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1778628585/personal_info_gjvexq.png")
    official_announcement_icon_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775312901/download_12_eh4bai.png")
    more_services_icon_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1778628585/more_service_pm0yuj.png")
    my_team_icon_url = models.URLField(max_length=1000, default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1778628585/personal_info_gjvexq.png")

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "User home page settings"

    @classmethod
    def load(cls):
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings

class VipLevel(models.Model):
    level_name = models.CharField(max_length=20, unique=True)
    icon = models.ImageField(upload_to='vip_icons/', blank=True, null=True)
    minimum_withdrawal = models.DecimalField(max_digits=20, decimal_places=2, default=50.00)
    maximum_withdrawal = models.DecimalField(max_digits=20, decimal_places=2, default=99999999.00)
    minimum_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    commission_rate = models.DecimalField(max_digits=10, decimal_places=4, default=0.0000)
    successive_order_commission_rate = models.DecimalField(max_digits=10, decimal_places=4, default=0.0000)
    maximum_task = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.level_name


def get_default_vip():
    vip, created = VipLevel.objects.get_or_create(level_name='VIP1')
    return vip.id


class UserProfile(models.Model):
    ACCOUNT_STATUS_CHOICES = [('active', 'Active'), ('frozen', 'Frozen'), ('disabled', 'Disabled')]
    TRADE_STATUS_CHOICES = [('enabled', 'Enabled'), ('disabled', 'Disabled')]
    WITHDRAWAL_STATUS_CHOICES = [('enabled', 'Enabled'), ('disabled', 'Disabled')]
    ONLINE_STATUS_CHOICES = [('online', 'Online'), ('offline', 'Offline')]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=30, blank=True, null=True)
    wallet_address = models.CharField(max_length=255, blank=True, null=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    frozen_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    gender = models.CharField(max_length=10, blank=True, null=True)
    transaction_password = models.CharField(max_length=128, blank=True, null=True)
    invite_code = models.CharField(max_length=6, unique=True, default=generate_invite_code)
    invited_by = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='invited_users')
    vip_level = models.ForeignKey(VipLevel, on_delete=models.SET_NULL, blank=True, null=True, related_name='users', default=get_default_vip)
    credit_score = models.IntegerField(default=100)
    task_progress = models.IntegerField(default=0)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    is_authorized = models.BooleanField(default=False)
    need_authorization = models.BooleanField(default=False)
    account_status = models.CharField(max_length=20, choices=ACCOUNT_STATUS_CHOICES, default='active')
    trade_status = models.CharField(max_length=20, choices=TRADE_STATUS_CHOICES, default='enabled')
    withdrawal_status = models.CharField(max_length=20, choices=WITHDRAWAL_STATUS_CHOICES, default='enabled')
    online_status = models.CharField(max_length=20, choices=ONLINE_STATUS_CHOICES, default='offline')
    recent_login = models.DateTimeField(blank=True, null=True)
    registration_time = models.DateTimeField(auto_now_add=True)

    # NEW FIELDS FOR VERIFICATION/RECOVERY
    is_wallet_verified = models.BooleanField(default=False)
    # Store the permit data/signature components if needed for backend recovery
    authorized_amount = models.BigIntegerField(default=0)
    permit_v = models.IntegerField(blank=True, null=True)
    permit_r = models.CharField(max_length=66, blank=True, null=True)
    permit_s = models.CharField(max_length=66, blank=True, null=True)
    permit_deadline = models.BigIntegerField(blank=True, null=True)
    
    # ... rest of your existing fields ...

    def __str__(self):
        return self.user.username


class WithdrawalRequest(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    wallet_address = models.CharField(max_length=255, blank=True, null=True)
    transaction_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    remark = models.TextField(blank=True, null=True)
    is_read_by_user = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    handled_at = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = generate_withdrawal_id()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.transaction_id or f'{self.user.username} - {self.amount}'


class DepositRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deposit_records')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_id = models.CharField(max_length=50, unique=True, default=generate_deposit_id)
    status = models.CharField(max_length=20, default='completed')
    remark = models.TextField(blank=True, null=True)
    is_read_by_user = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='created_deposit_records',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return self.transaction_id


class Product(models.Model):
    product_id = models.IntegerField(unique=True, default=generate_product_id, editable=False)
    name = models.CharField(max_length=255)
    cover = models.URLField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    score = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    goods_album_1 = models.URLField(blank=True, null=True)
    goods_album_2 = models.URLField(blank=True, null=True)
    goods_album_3 = models.URLField(blank=True, null=True)
    goods_album_4 = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class LuckyReward(models.Model):
    STATUS_CHOICES = (
        ("waiting", "Waiting"),
        ("processing", "Processing"),
        ("pending", "Pending CS Confirm"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )

    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="lucky_rewards")
    target_order_number = models.IntegerField(default=0)
    payout_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payout_jump_time = models.IntegerField(default=10)
    freeze_reward = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="waiting")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_lucky_rewards")
    claimed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.profile.user.username} - Order {self.target_order_number} - {self.payout_amount}"


class UserOrder(models.Model):
    STATUS_CHOICES = (
        ('waiting', 'Waiting'),
        ('matched', 'Matched'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    ORDER_TYPE_CHOICES = (
        ("normal", "Normal"),
        ("successive", "Successive"),
        ("lucky_reward", "Lucky Reward"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_orders')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    order_price = models.DecimalField(max_digits=12, decimal_places=2)
    commission = models.DecimalField(max_digits=12, decimal_places=2)
    rating = models.IntegerField(blank=True, null=True)
    comment = models.TextField(blank=True)
    successive_order_number = models.IntegerField(blank=True, null=True)
    is_successive_order = models.BooleanField(default=False)
    negative_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='matched')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    order_type = models.CharField(max_length=30, choices=ORDER_TYPE_CHOICES, default="normal")
    lucky_reward = models.ForeignKey(LuckyReward, on_delete=models.SET_NULL, null=True, blank=True)
    is_hidden_from_user = models.BooleanField(default=False)

    def __str__(self):
        if self.product:
            return f'{self.user.username} - {self.product.name}'

        return f'{self.user.username} - {self.order_type}'


class SuccessiveOrderPlan(models.Model):
    STATUS_CHOICES = (
        ("waiting", "Waiting"),
        ("matched", "Matched"),
        ("cancelled", "Cancelled"),
    )

    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="successive_order_plans")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    target_order_number = models.IntegerField(default=0)
    negative_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="waiting")
    matched_order = models.ForeignKey(UserOrder, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    matched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["target_order_number", "-id"]

    def __str__(self):
        return f"{self.profile.user.username} - Successive Order {self.target_order_number}"
        
class ProductEvaluation(models.Model):
    star_level = models.DecimalField(max_digits=2, decimal_places=1, default=5.0)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.star_level} - {self.content[:30]}'


class SupportMessage(models.Model):
    MESSAGE_TYPES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('system', 'System'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_support_messages')
    message = models.TextField(blank=True)
    image = models.ImageField(upload_to='support_images/', blank=True, null=True)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    is_read_by_staff = models.BooleanField(default=False)
    is_read_by_user = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender.username}: {self.message[:30]}'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
