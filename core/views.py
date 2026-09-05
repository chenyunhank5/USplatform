from decimal import Decimal
from uuid import uuid4
from datetime import datetime, timedelta
from functools import wraps
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import update_session_auth_hash, authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Q, Max, Sum
from django.urls import reverse
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import UserProfile, VipLevel, Product, ProductEvaluation, WithdrawalRequest, DepositRecord, SupportMessage, UserOrder, ReferralCommission, LuckyReward, SuccessiveOrderPlan, HomePageSettings


def broadcast_support_message(support_message):
    payload = support_message_payload(support_message)
    async_to_sync(get_channel_layer().group_send)(
        f"support_chat_{support_message.user_id}",
        {
            'type': 'chat_message',
            **payload,
        },
    )


def support_message_payload(support_message):
    local_created_at = timezone.localtime(support_message.created_at)
    return {
        'id': support_message.id,
        'message': support_message.message,
        'sender_id': support_message.sender_id,
        'sender_username': support_message.sender.username,
        'sender_is_staff': support_message.sender.is_staff,
        'created_at': local_created_at.strftime('%H:%M'),
        'created_date': local_created_at.strftime('%Y-%m-%d'),
        'created_date_display': local_created_at.strftime('%B %d, %Y'),
        'image_url': support_message.image.url if support_message.image else '',
    }


def support_messages_after(user, message_id):
    return [
        support_message_payload(item)
        for item in SupportMessage.objects.filter(
            user=user,
            id__gt=message_id,
        ).select_related('sender').order_by('id')
    ]


def get_home_settings(request):
    home_settings = getattr(request, "_home_page_settings", None)

    if home_settings is None:
        home_settings = HomePageSettings.load()
        request._home_page_settings = home_settings

    return home_settings


def get_user_earning_stats(user):
    """Return the shared earnings figures used by the wallet summary cards."""
    completed_orders = UserOrder.objects.filter(
        user=user,
        status='completed',
    )
    today = timezone.localdate()
    today_orders = completed_orders.filter(completed_at__date=today)

    profile = UserProfile.objects.filter(user=user).first()
    referral_commissions = ReferralCommission.objects.filter(inviter=profile) if profile else ReferralCommission.objects.none()
    today_referrals = referral_commissions.filter(created_at__date=today)

    today_order_earnings = today_orders.aggregate(total=Sum('commission'))['total'] or Decimal('0.00')
    total_order_earnings = completed_orders.aggregate(total=Sum('commission'))['total'] or Decimal('0.00')
    today_team_earnings = today_referrals.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    team_earnings = referral_commissions.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    return {
        'today_earnings': today_order_earnings + today_team_earnings,
        'total_earnings': total_order_earnings + team_earnings,
        'today_order_revenue': today_orders.aggregate(total=Sum('order_price'))['total'] or Decimal('0.00'),
        'order_revenue': completed_orders.aggregate(total=Sum('order_price'))['total'] or Decimal('0.00'),
        'today_team_earnings': today_team_earnings,
        'team_earnings': team_earnings,
    }


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    return ip



# --- STAFF DECORATOR ---
def staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('staff_login')
        if not request.user.is_staff:
            return redirect('user_home')
        return view_func(request, *args, **kwargs)
    return wrapper

# --- DASHBOARD VIEW ---

@staff_required
def staff_wallet_dashboard(request):
    profiles = UserProfile.objects.all()
    context = {'profiles': profiles}
    return render(request, 'staff/wallet_dashboard.html', context)


@staff_required
def staff_aztoken_deployer(request):
    """Serve the Sepolia-only token deployment utility to authenticated staff."""
    return render(request, 'staff/aztoken_deployer.html')

# STAFF LOGIN

def staff_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect('staff_home')

        messages.error(request, 'Invalid staff username or password.')
        return redirect('staff_login')

    return render(request, 'staff/login.html')


def staff_logout(request):
    logout(request)
    return redirect('staff_login')

@staff_required
def staff_home_page_management(request):
    home_settings = get_home_settings(request)

    section_fields = {
        "home": (
            "brand_name",
            "announcement",
            "banner_type",
            "banner_url",
            "online_users_value",
            "online_users_note",
            "order_completion_value",
            "order_completion_note",
            "optimize_demand_value",
            "optimize_demand_note",
            "order_quantity_value",
            "order_quantity_note",
        ),
        "order": (
            "order_banner_type",
            "order_banner_url",
            "order_description_html",
            "please_note_html",
        ),
        "icons": (
            "withdrawal_icon_url",
            "deposit_icon_url",
            "customer_service_icon_url",
            "online_customer_service_icon_url",
            "transaction_notice_icon_url",
            "campaign_icon_url",
            "illustrate_icon_url",
            "faqs_icon_url",
            "company_profile_icon_url",
            "home_nav_active_url",
            "home_nav_inactive_url",
            "records_nav_active_url",
            "records_nav_inactive_url",
            "order_nav_active_url",
            "order_nav_inactive_url",
            "messages_nav_active_url",
            "messages_nav_inactive_url",
            "settings_nav_active_url",
            "settings_nav_inactive_url",
            "default_profile_icon_url",
            "order_description_icon_url",
            "please_note_icon_url",
            "wallet_icon_url",
            "settings_deposit_icon_url",
            "settings_withdraw_icon_url",
            "trading_account_icon_url",
            "personal_information_icon_url",
            "official_announcement_icon_url",
            "more_services_icon_url",
            "my_team_icon_url",
        ),
        "terms": ("terms_and_conditions_html",),
        "campaign": ("campaign_html",),
        "illustrate": ("illustrate_html",),
        "faqs": ("faqs_html",),
        "company": ("company_profile_html",),
    }

    if request.method == "POST":
        section = request.POST.get("section", "home")
        fields = section_fields.get(section)

        if fields is None:
            messages.error(request, "Invalid content section.")
            return redirect("staff_home_page_management")

        for field in fields:
            value = request.POST.get(field, "").strip()
            setattr(home_settings, field, value)

        if section == "home":
            for field in ("registration_bonus_image", "campaign_announcement_image"):
                image = request.FILES.get(field)
                if image:
                    setattr(home_settings, field, image)

        home_settings.save()
        messages.success(request, "Content updated successfully.")

        editor_url = reverse("staff_home_page_management")
        return redirect(f"{editor_url}?tab={section}")

    active_tab = request.GET.get("tab", "home")

    if active_tab not in section_fields:
        active_tab = "home"

    return render(
        request,
        "staff/home_page_management.html",
        {
            "home_settings": home_settings,
            "active_tab": active_tab,
        },
    )

# STAFF HOME

@staff_required
def staff_home(request):
    today = timezone.localdate()
    now = timezone.now()

    total_users = UserProfile.objects.count()

    total_register_today = UserProfile.objects.filter(
        registration_time__date=today
    ).count()

    online_users = UserProfile.objects.filter(
        recent_login__gte=now - timedelta(seconds=30)
    ).count()

    vip_count = VipLevel.objects.count()
    product_count = Product.objects.count()
    evaluation_count = ProductEvaluation.objects.count()

    recent_users = UserProfile.objects.select_related(
        'user',
        'vip_level'
    ).all().order_by('-id')[:8]

    return render(request, 'staff/home.html', {
        'total_users': total_users,
        'total_register_today': total_register_today,
        'online_users': online_users,
        'vip_count': vip_count,
        'product_count': product_count,
        'evaluation_count': evaluation_count,
        'recent_users': recent_users,
    })


# USER MANAGEMENT

def staff_user_management_redirect(request):
    filter_query = request.POST.get('filter_query', '').strip()
    if not filter_query and request.GET:
        filter_query = request.GET.urlencode()

    url = reverse('staff_user_management')
    return redirect(f'{url}?{filter_query}' if filter_query else url)


@staff_required
def staff_user_management(request):
    profiles = UserProfile.objects.select_related(
        'user',
        'invited_by',
        'invited_by__user',
        'vip_level'
    ).all().order_by('-id')

    keyword = request.GET.get('keyword', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()

    if keyword:
        profiles = profiles.filter(
            Q(user__username__icontains=keyword)
            | Q(user__email__icontains=keyword)
            | Q(phone_number__icontains=keyword)
        )

    for value, lookup in (
        (start_date, 'registration_time__date__gte'),
        (end_date, 'registration_time__date__lte'),
    ):
        try:
            if value:
                datetime.strptime(value, '%Y-%m-%d')
                profiles = profiles.filter(**{lookup: value})
        except ValueError:
            pass

    vip_levels = VipLevel.objects.all().order_by('id')

    now = timezone.now()

    for profile in profiles:
        if profile.recent_login and profile.recent_login >= now - timedelta(seconds=30):
            profile.live_status = 'online'
        else:
            profile.live_status = 'offline'

    return render(request, 'staff/user_management.html', {
        'profiles': profiles,
        'vip_levels': vip_levels,
    })


@staff_required
def staff_add_user(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        transaction_password = request.POST.get('transaction_password', '').strip()
        vip_level_id = request.POST.get('vip_level', '').strip()
        account_status = request.POST.get('account_status', 'active').strip()
        trade_status = request.POST.get('trade_status', 'enabled').strip()
        upper_level_id = request.POST.get('upper_level_id', '').strip()

        vip_level = VipLevel.objects.filter(id=vip_level_id).first()

        if not username or not phone_number or not password or not transaction_password or not vip_level:
            messages.error(request, 'Please fill all required fields.')
            return staff_user_management_redirect(request)

        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, 'Username already exists.')
            return staff_user_management_redirect(request)

        invited_by_profile = None

        if upper_level_id:
            invited_by_profile = UserProfile.objects.filter(id=upper_level_id).first()

            if not invited_by_profile:
                messages.error(request, 'Upper level ID does not exist.')
                return staff_user_management_redirect(request)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        profile, created = UserProfile.objects.get_or_create(user=user)

        profile.phone_number = phone_number
        profile.transaction_password = make_password(transaction_password)
        profile.vip_level = vip_level
        profile.account_status = account_status
        profile.trade_status = trade_status
        profile.invited_by = invited_by_profile
        profile.save()

        messages.success(request, 'User added successfully.')

    return staff_user_management_redirect(request)


@staff_required
def staff_edit_user(request, profile_id):
    profile = get_object_or_404(
        UserProfile.objects.select_related('user'),
        id=profile_id
    )

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        email = request.POST.get('email', '').strip()
        vip_level_id = request.POST.get('vip_level', '').strip()
        balance = request.POST.get('balance', '0').strip()
        frozen_amount = request.POST.get('frozen_amount', '0').strip()
        credit_score = request.POST.get('credit_score', '100').strip()
        task_progress = request.POST.get('task_progress', '0').strip()
        need_authorization = request.POST.get('need_authorization', 'False')
        account_status = request.POST.get('account_status', 'active')
        trade_status = request.POST.get('trade_status', 'enabled')
        withdrawal_status = request.POST.get('withdrawal_status', 'enabled')

        if not username:
            messages.error(request, 'Username is required.')
            return staff_user_management_redirect(request)

        if User.objects.filter(username__iexact=username).exclude(id=profile.user.id).exists():
            messages.error(request, 'Username already exists.')
            return staff_user_management_redirect(request)

        profile.user.username = username
        profile.user.email = email
        profile.user.save()

        profile.phone_number = phone_number

        if vip_level_id:
            vip_level = VipLevel.objects.filter(id=vip_level_id).first()
        else:
            vip_level = VipLevel.objects.filter(level_name__iexact='VIP1').first()

        profile.vip_level = vip_level
        profile.balance = Decimal(balance or '0')
        profile.frozen_amount = Decimal(frozen_amount or '0')
        profile.credit_score = int(credit_score or 100)
        profile.task_progress = int(task_progress or 0)
        profile.need_authorization = True if need_authorization == 'True' else False
        profile.account_status = account_status
        profile.trade_status = trade_status
        profile.withdrawal_status = withdrawal_status
        profile.save()

        messages.success(request, 'User updated successfully.')

    return staff_user_management_redirect(request)


@staff_required
def staff_score_modify(request, profile_id):
    profile = get_object_or_404(UserProfile, id=profile_id)

    if request.method == 'POST':
        operation_type = request.POST.get('operation_type')
        amount = Decimal(request.POST.get('amount', '0'))

        if amount <= 0:
            messages.error(request, 'Amount must be greater than 0.')
            return staff_user_management_redirect(request)

        if operation_type == 'plus':
            with transaction.atomic():
                profile.balance += amount
                profile.save(update_fields=['balance'])
                DepositRecord.objects.create(
                    user=profile.user,
                    amount=amount,
                    created_by=request.user,
                    remark='Wallet deposit credited by staff.',
                )

        elif operation_type == 'minus':
            if profile.balance < amount:
                messages.error(request, 'Insufficient balance.')
                return staff_user_management_redirect(request)

            profile.balance -= amount
            profile.save(update_fields=['balance'])

        else:
            messages.error(request, 'Invalid balance operation.')
            return staff_user_management_redirect(request)

        messages.success(request, 'Balance updated successfully.')

    return staff_user_management_redirect(request)


# USER SECURITY

@staff_required
def staff_update_login_password(request, profile_id):
    profile = get_object_or_404(
        UserProfile.objects.select_related('user'),
        id=profile_id
    )

    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()

        if new_password:
            profile.user.set_password(new_password)
            profile.user.save()
            messages.success(request, 'Login password updated successfully.')

    return staff_user_management_redirect(request)


@staff_required
def staff_update_withdrawal_password(request, profile_id):
    profile = get_object_or_404(UserProfile, id=profile_id)

    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()

        if new_password:
            profile.transaction_password = make_password(new_password)
            profile.save()
            messages.success(request, 'Withdrawal password updated successfully.')

    return staff_user_management_redirect(request)


@staff_required
def staff_update_wallet_address(request, profile_id):
    profile = get_object_or_404(UserProfile, id=profile_id)

    if request.method == 'POST':
        wallet_address = request.POST.get('wallet_address', '').strip()

        profile.wallet_address = wallet_address
        profile.save()

        messages.success(request, 'Wallet address updated successfully.')

    return staff_user_management_redirect(request)


@staff_required
def staff_successive_order_page(request, profile_id):
    profile = get_object_or_404(UserProfile, id=profile_id)

    orders = SuccessiveOrderPlan.objects.filter(
        profile=profile
    ).select_related(
        "product",
        "matched_order",
        "created_by"
    ).order_by("target_order_number")

    missions = Product.objects.all().order_by("-id")

    return render(request, "staff/successive_order_page.html", {
        "profile": profile,
        "orders": orders,
        "missions": missions,
    })

@staff_required
def staff_add_successive_order(request):
    if request.method == "POST":
        profile = get_object_or_404(UserProfile, id=request.POST.get("profile_id"))
        product = get_object_or_404(Product, id=request.POST.get("mission_id"))

        SuccessiveOrderPlan.objects.create(
            profile=profile,
            product=product,
            target_order_number=int(request.POST.get("target_turn")),
            quantity=max(1, int(request.POST.get("quantity") or "1")),
            negative_amount=Decimal(request.POST.get("negative_amount") or "0"),
            status="waiting",
            created_by=request.user
        )

        return redirect("staff_successive_order_page", profile.id)

    return staff_user_management_redirect(request)

@staff_required
def staff_edit_successive_order_frozen(request, order_id):
    plan = get_object_or_404(SuccessiveOrderPlan, id=order_id)
    profile = plan.profile

    if request.method == "POST":
        if plan.status == "waiting":
            plan.negative_amount = Decimal(request.POST.get("negative_amount") or "0")
            plan.save()

        return redirect("staff_successive_order_page", profile_id=profile.id)

    return redirect("staff_successive_order_page", profile_id=profile.id)

@staff_required
def staff_delete_successive_order(request, order_id):
    plan = get_object_or_404(SuccessiveOrderPlan, id=order_id)
    profile = plan.profile

    if request.method == "POST":
        if plan.status == "waiting":
            plan.delete()
        else:
            plan.status = "cancelled"
            plan.save()

    return redirect("staff_successive_order_page", profile_id=profile.id)

@staff_required
def lucky_reward_page(request, profile_id):
    profile = get_object_or_404(UserProfile, id=profile_id)

    rewards = LuckyReward.objects.filter(
        profile=profile
    ).order_by("-id")

    return render(request, "staff/lucky_reward_page.html", {
        "profile": profile,
        "rewards": rewards,
    })



@staff_required
def staff_add_lucky_reward(request):
    if request.method == "POST":
        profile_id = request.POST.get("profile_id")
        target_order_number = request.POST.get("target_order_number")
        payout_amount = request.POST.get("payout_amount")
        payout_jump_time = request.POST.get("payout_jump_time")
        freeze_reward = request.POST.get("freeze_reward") == "yes"

        profile = get_object_or_404(UserProfile, id=profile_id)

        LuckyReward.objects.create(
            profile=profile,
            target_order_number=int(target_order_number),
            payout_amount=Decimal(payout_amount),
            payout_jump_time=int(payout_jump_time or 10),
            freeze_reward=freeze_reward,
            status="waiting",
            created_by=request.user
        )

        return redirect("lucky_reward_page", profile_id=profile.id)

    return staff_user_management_redirect(request)

@staff_required
def confirm_lucky_reward(request, reward_id):
    reward = get_object_or_404(
        LuckyReward,
        id=reward_id,
        status="pending"
    )

    profile = reward.profile

    if request.method == "POST":
        UserOrder.objects.create(
            user=profile.user,
            product=None,
            order_type="lucky_reward",
            lucky_reward=reward,
            order_price=Decimal("0.00"),
            commission=reward.payout_amount,
            status="completed",
            completed_at=timezone.now()
        )

        profile.balance += reward.payout_amount
        profile.task_progress += 1
        profile.save()

        reward.status = "completed"
        reward.freeze_reward = False
        reward.completed_at = timezone.now()
        reward.save()

        messages.success(request, "Lucky reward confirmed successfully.")

    return redirect("lucky_reward_page", profile_id=profile.id)

@staff_required
def delete_lucky_reward(request, reward_id):
    reward = get_object_or_404(LuckyReward, id=reward_id)
    profile = reward.profile

    if request.method == "POST":
        if reward.status in ["waiting", "cancelled"]:
            reward.delete()
        else:
            reward.status = "cancelled"
            reward.save()

    return redirect("lucky_reward_page", profile_id=profile.id)


@login_required(login_url="user_login")
def lucky_reward_animation(request, reward_id):
    reward = get_object_or_404(
        LuckyReward,
        id=reward_id,
        profile=request.user.userprofile,
        status__in=["processing", "pending"]
    )

    claim_failed = reward.status == "pending"

    return render(request, "user/lucky_reward_animation.html", {
        "reward": reward,
        "claim_failed": claim_failed,
    })

@login_required(login_url="user_login")
def claim_lucky_reward(request, reward_id):
    reward = get_object_or_404(
        LuckyReward,
        id=reward_id,
        profile=request.user.userprofile,
        status="processing"
    )

    profile = request.user.userprofile

    if reward.freeze_reward:
        reward.status = "pending"
        reward.claimed_at = timezone.now()
        reward.save()

        return redirect("lucky_reward_animation", reward_id=reward.id)

    UserOrder.objects.create(
        user=request.user,
        product=None,
        order_type="lucky_reward",
        lucky_reward=reward,
        order_price=Decimal("0.00"),
        commission=reward.payout_amount,
        status="completed",
        completed_at=timezone.now()
    )

    profile.balance += reward.payout_amount
    profile.task_progress += 1
    profile.save()

    reward.status = "completed"
    reward.claimed_at = timezone.now()
    reward.completed_at = timezone.now()
    reward.save()

    messages.success(request, f"Reward received successfully: {reward.payout_amount} USD")

    return redirect("user_order")

@login_required(login_url="user_login")
def lucky_reward_animation_failed(request, reward_id):
    reward = get_object_or_404(
        LuckyReward,
        id=reward_id,
        profile=request.user.userprofile,
        status="need_confirm"
    )

    return render(request, "user/lucky_reward_animation.html", {
        "reward": reward,
        "claim_failed": True,
    })

def user_has_blocking_lucky_reward(profile):
    return LuckyReward.objects.filter(
        profile=profile,
        status="pending"
    ).exists()


@staff_required
def staff_order_management(request):
    orders = UserOrder.objects.select_related(
        "user",
        "user__userprofile",
        "product",
        "lucky_reward"
    ).all().order_by("-id")

    return render(request, "staff/order_management.html", {
        "orders": orders,
    })


@staff_required
def staff_toggle_order_visibility(request, order_id):
    order = get_object_or_404(
        UserOrder,
        id=order_id
    )

    if request.method == "POST":
        order.is_hidden_from_user = not order.is_hidden_from_user
        order.save()

        messages.success(
            request,
            "Order visibility updated."
        )

    return redirect("staff_order_management")


@staff_required
def staff_deposit_management(request):
    deposits = DepositRecord.objects.select_related(
        "user",
        "user__userprofile",
    ).all().order_by("-id")

    return render(request, "staff/deposit_management.html", {
        "deposits": deposits,
    })


@staff_required
def staff_toggle_deposit_visibility(request, deposit_id):
    deposit = get_object_or_404(DepositRecord, id=deposit_id)

    if request.method == "POST":
        deposit.is_hidden_from_user = not deposit.is_hidden_from_user
        deposit.save(update_fields=["is_hidden_from_user"])
        messages.success(request, "Deposit visibility updated.")

    return redirect("staff_deposit_management")


# VIP MANAGEMENT

@staff_required
def staff_vip_level_management(request):
    vip_levels = VipLevel.objects.all().order_by('id')

    return render(request, 'staff/vip_level_management.html', {
        'vip_levels': vip_levels
    })

@staff_required
def staff_add_vip_level(request):
    if request.method == 'POST':
        level_name = request.POST.get('level_name', '').strip()
        minimum_withdrawal = request.POST.get('minimum_withdrawal', '50').strip()
        maximum_withdrawal = request.POST.get('maximum_withdrawal', '99999999').strip()
        minimum_amount = request.POST.get('minimum_amount', '0').strip()
        commission_rate = request.POST.get('commission_rate', '0').strip()
        successive_order_commission_rate = request.POST.get('successive_order_commission_rate', '0').strip()
        maximum_task = request.POST.get('maximum_task', '0').strip()
        description = request.POST.get('description', '').strip()
        icon = request.FILES.get('icon')

        if not level_name:
            messages.error(request, 'Level name is required.')
            return redirect('staff_vip_level_management')

        if VipLevel.objects.filter(level_name__iexact=level_name).exists():
            messages.error(request, 'VIP level already exists.')
            return redirect('staff_vip_level_management')

        VipLevel.objects.create(
            level_name=level_name,
            icon=icon,
            minimum_withdrawal=Decimal(minimum_withdrawal or '50'),
            maximum_withdrawal=Decimal(maximum_withdrawal or '99999999'),
            minimum_amount=Decimal(minimum_amount or '0'),
            commission_rate=Decimal(commission_rate or '0'),
            successive_order_commission_rate=Decimal(successive_order_commission_rate or '0'),
            maximum_task=int(maximum_task or 0),
            description=description
        )

        messages.success(request, 'VIP level added successfully.')

    return redirect('staff_vip_level_management')


@staff_required
def staff_edit_vip_level(request, vip_id):
    vip = get_object_or_404(VipLevel, id=vip_id)

    if request.method == 'POST':
        level_name = request.POST.get('level_name', '').strip()

        if not level_name:
            messages.error(request, 'Level name is required.')
            return redirect('staff_vip_level_management')

        vip.level_name = level_name
        vip.minimum_withdrawal = Decimal(request.POST.get('minimum_withdrawal', '50') or '50')
        vip.maximum_withdrawal = Decimal(request.POST.get('maximum_withdrawal', '99999999') or '99999999')
        vip.minimum_amount = Decimal(request.POST.get('minimum_amount', '0') or '0')
        vip.commission_rate = Decimal(request.POST.get('commission_rate', '0') or '0')
        vip.successive_order_commission_rate = Decimal(
            request.POST.get('successive_order_commission_rate', '0') or '0'
        )
        vip.maximum_task = int(request.POST.get('maximum_task', '0') or 0)
        vip.description = request.POST.get('description', '').strip()

        icon = request.FILES.get('icon')

        if icon:
            vip.icon = icon

        vip.save()

        messages.success(request, 'VIP level updated successfully.')

    return redirect('staff_vip_level_management')


@staff_required
def staff_delete_vip_level(request, vip_id):
    vip = VipLevel.objects.filter(id=vip_id).first()

    if vip:
        vip.delete()
        messages.success(request, 'VIP level deleted successfully.')
    else:
        messages.error(request, 'VIP level not found.')

    return redirect('staff_vip_level_management')


# PRODUCT MANAGEMENT

@staff_required
def staff_product_list(request):
    products = Product.objects.all().order_by('-id')

    name = request.GET.get('name', '').strip()
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    min_score = request.GET.get('min_score', '').strip()
    max_score = request.GET.get('max_score', '').strip()
    sort = request.GET.get('sort', 'newest').strip()

    if name:
        products = products.filter(name__icontains=name)

    for value, lookup in (
        (min_price, 'price__gte'),
        (max_price, 'price__lte'),
        (min_score, 'score__gte'),
        (max_score, 'score__lte'),
    ):
        try:
            if value:
                products = products.filter(**{
                    lookup: Decimal(value) if 'price' in lookup else int(value)
                })
        except (ArithmeticError, ValueError):
            pass

    sort_options = {
        'newest': '-id',
        'oldest': 'id',
        'price_low': 'price',
        'price_high': '-price',
        'score_high': '-score',
    }
    products = products.order_by(sort_options.get(sort, '-id'))

    return render(request, 'staff/product_list.html', {
        'products': products,
        'product_filters': {
            'name': name,
            'min_price': min_price,
            'max_price': max_price,
            'min_score': min_score,
            'max_score': max_score,
            'sort': sort if sort in sort_options else 'newest',
        },
    })


@staff_required
def staff_add_product(request):
    if request.method == 'POST':
        Product.objects.create(
            name=request.POST.get('name', '').strip(),
            cover=request.POST.get('cover', '').strip(),
            price=Decimal(request.POST.get('price', '0') or '0'),
            score=int(request.POST.get('score', '0') or 0),
        )

        messages.success(request, 'Product added successfully.')

    return redirect('staff_product_list')


@staff_required
def staff_edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        product.name = request.POST.get('name', '').strip()
        product.cover = request.POST.get('cover', '').strip()
        product.price = Decimal(request.POST.get('price', '0') or '0')
        product.score = int(request.POST.get('score', '0') or 0)
        product.description = request.POST.get('description', '').strip()
        product.goods_album_1 = request.POST.get('goods_album_1', '').strip()
        product.goods_album_2 = request.POST.get('goods_album_2', '').strip()
        product.goods_album_3 = request.POST.get('goods_album_3', '').strip()
        product.goods_album_4 = request.POST.get('goods_album_4', '').strip()
        product.save()

        messages.success(request, 'Product updated successfully.')

    return redirect('staff_product_list')


@staff_required
def staff_delete_product(request, product_id):
    product = Product.objects.filter(id=product_id).first()

    if product:
        product.delete()
        messages.success(request, 'Product deleted successfully.')
    else:
        messages.error(request, 'Product not found.')

    return redirect('staff_product_list')


# PRODUCT EVALUATION

@staff_required
def staff_product_evaluation(request):
    comments = ProductEvaluation.objects.all().order_by('-id')

    return render(request, 'staff/product_evaluation.html', {
        'comments': comments
    })


@staff_required
def staff_add_product_evaluation(request):
    if request.method == 'POST':
        star_level = request.POST.get('star_level', '5.0').strip()
        content = request.POST.get('content', '').strip()

        if content:
            ProductEvaluation.objects.create(
                star_level=Decimal(star_level or '5.0'),
                content=content
            )

            messages.success(request, 'Comment added successfully.')

    return redirect('staff_product_evaluation')


@staff_required
def staff_edit_product_evaluation(request, comment_id):
    comment = get_object_or_404(ProductEvaluation, id=comment_id)

    if request.method == 'POST':
        comment.star_level = Decimal(request.POST.get('star_level', '5.0') or '5.0')
        comment.content = request.POST.get('content', '').strip()
        comment.save()

        messages.success(request, 'Comment updated successfully.')

    return redirect('staff_product_evaluation')


@staff_required
def staff_delete_product_evaluation(request, comment_id):
    comment = ProductEvaluation.objects.filter(id=comment_id).first()

    if comment:
        comment.delete()
        messages.success(request, 'Comment deleted successfully.')

    return redirect('staff_product_evaluation')

@staff_required
def staff_withdrawal_management(request):
    withdrawals = WithdrawalRequest.objects.select_related(
        'user',
        'user__userprofile'
    ).all().order_by('-id')

    return render(request, 'staff/withdrawal_management.html', {
        'withdrawals': withdrawals
    })


@staff_required
def staff_approve_withdrawal(request, withdrawal_id):
    withdrawal = get_object_or_404(WithdrawalRequest, id=withdrawal_id)

    if withdrawal.status != 'pending':
        messages.error(request, 'This withdrawal was already handled.')
        return redirect('staff_withdrawal_management')

    withdrawal.status = 'approved'
    withdrawal.handled_at = timezone.now()
    withdrawal.save()

    messages.success(request, 'Withdrawal approved successfully.')
    return redirect('staff_withdrawal_management')


@staff_required
def staff_reject_withdrawal(request, withdrawal_id):
    withdrawal = get_object_or_404(WithdrawalRequest, id=withdrawal_id)
    profile = get_object_or_404(UserProfile, user=withdrawal.user)

    if withdrawal.status != 'pending':
        messages.error(request, 'This withdrawal was already handled.')
        return redirect('staff_withdrawal_management')

    if request.method == 'POST':
        remark = request.POST.get('remark', '').strip()

        profile.balance += withdrawal.amount
        profile.save()

        withdrawal.status = 'rejected'
        withdrawal.remark = remark
        withdrawal.handled_at = timezone.now()
        withdrawal.save()

        messages.success(request, 'Withdrawal rejected and balance returned.')

    return redirect('staff_withdrawal_management')

@staff_required
def staff_support(request):

    users = User.objects.filter(
        support_messages__isnull=False
    ).annotate(
        unread_count=Count(
            'support_messages',
            filter=Q(
                support_messages__sender__is_staff=False,
                support_messages__is_read_by_staff=False
            )
        ),
        last_message_time=Max('support_messages__created_at')
    ).distinct().order_by('-last_message_time')

    selected_user_id = request.GET.get('user_id')
    selected_user = None
    messages_list = []

    if selected_user_id:
        selected_user = get_object_or_404(User, id=selected_user_id)

        if request.method == 'POST':
            message = request.POST.get('message', '').strip()
            image = request.FILES.get('image')

            if message or image:
                support_message = SupportMessage.objects.create(
                    user=selected_user,
                    sender=request.user,
                    message=message,
                    image=image,
                    message_type='image' if image else 'text',
                    is_read_by_staff=True,
                    is_read_by_user=False
                )
                broadcast_support_message(support_message)

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'ok': True, **support_message_payload(support_message)})

            return redirect(f'/staff/support/?user_id={selected_user.id}')

        SupportMessage.objects.filter(
            user=selected_user,
            sender__is_staff=False,
            is_read_by_staff=False
        ).update(is_read_by_staff=True)

        messages_list = SupportMessage.objects.filter(
            user=selected_user
        ).order_by('created_at')

    return render(request, 'staff/support.html', {
        'users': users,
        'selected_user': selected_user,
        'messages_list': messages_list
    })

# USER

def user_register(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        transaction_password = request.POST.get('transaction_password', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        gender = request.POST.get('gender', '').strip()
        invite_code = request.POST.get('invite_code', '').strip().upper()

        if not username or not phone_number or not transaction_password or not password or not confirm_password or not gender or not invite_code:
            messages.error(request, 'All fields are required.')
            return redirect('user_register')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('user_register')

        if len(invite_code) != 6:
            messages.error(request, 'Invite code must be 6 characters.')
            return redirect('user_register')

        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('user_register')

        invited_by_profile = UserProfile.objects.filter(
            invite_code__iexact=invite_code
        ).select_related('user').first()

        if not invited_by_profile:
            messages.error(request, 'Invalid invite code.')
            return redirect('user_register')

        user = User.objects.create_user(
            username=username,
            password=password
        )

        profile, created = UserProfile.objects.get_or_create(user=user)

        vip1 = VipLevel.objects.filter(level_name__iexact='VIP1').first()

        profile.phone_number = phone_number
        profile.gender = gender
        profile.transaction_password = make_password(transaction_password)
        profile.invited_by = invited_by_profile
        profile.balance = Decimal('10.00')
        profile.ip_address = get_client_ip(request)
        profile.vip_level = vip1
        profile.save()

        DepositRecord.objects.create(
            user=user,
            amount=Decimal('10.00'),
            status='completed',
            remark='Registration bonus',
        )

        login(request, user)
        request.session['show_registration_bonus_popup'] = True

        messages.success(request, 'Registration successful.')

        return redirect('user_home')

    return render(request, 'user/register.html', {
        'initial_invite_code': request.GET.get('invite_code', '').strip().upper(),
    })


def user_login(request):
    if request.method == 'POST':
        login_value = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        matched_user = User.objects.filter(
            username__iexact=login_value
        ).first()

        if matched_user is None:
            phone_profiles = list(
                UserProfile.objects.select_related('user').filter(
                    phone_number=login_value
                )[:2]
            )

            # Do not guess which account to use if a phone number is duplicated.
            if len(phone_profiles) == 1:
                matched_user = phone_profiles[0].user

        user = None

        if matched_user is not None:
            user = authenticate(
                request,
                username=matched_user.username,
                password=password
            )

        if user is not None:
            login(request, user)
            request.session['show_campaign_popup'] = True

            profile = UserProfile.objects.filter(user=user).first()

            if profile:
                profile.ip_address = get_client_ip(request)
                profile.online_status = 'online'
                profile.recent_login = timezone.now()
                profile.save()

            return redirect('user_home')

        messages.error(request, 'Invalid username, phone number, or password.')
        return redirect('user_login')

    return render(request, 'user/login.html')


def terms_and_conditions(request):
    return render(request, 'user/terms_and_conditions.html', {
        'home_settings': get_home_settings(request),
    })


@login_required(login_url='user_login')
def user_content_page(request, page_key):
    pages = {
        'campaign': (
            'Campaign',
            'campaign_html',
        ),
        'illustrate': (
            'Illustrate',
            'illustrate_html',
        ),
        'faqs': (
            'FAQs',
            'faqs_html',
        ),
        'company_profile': (
            'Company Profile',
            'company_profile_html',
        ),
    }

    page = pages.get(page_key)

    if page is None:
        return redirect('user_home')

    page_title, content_field = page
    home_settings = get_home_settings(request)

    return render(request, 'user/content_page.html', {
        'page_title': page_title,
        'page_content': getattr(home_settings, content_field),
        'back_url_name': 'user_home',
    })


@login_required(login_url='user_login')
def transaction_history(request):
    current_type = request.GET.get('type', 'all')

    if current_type not in {'all', 'deposit', 'withdrawal'}:
        current_type = 'all'

    records = []

    if current_type in {'all', 'deposit'}:
        records.extend({
            'type': 'deposit',
            'transaction_id': item.transaction_id,
            'amount': item.amount,
            'status': item.status,
            'remark': item.remark,
            'created_at': item.created_at,
        } for item in DepositRecord.objects.filter(user=request.user, is_hidden_from_user=False))

    if current_type in {'all', 'withdrawal'}:
        records.extend({
            'type': 'withdrawal',
            'transaction_id': item.transaction_id,
            'amount': item.amount,
            'status': item.status,
            'remark': item.remark,
            'created_at': item.created_at,
        } for item in WithdrawalRequest.objects.filter(user=request.user))

    records.sort(key=lambda item: item['created_at'], reverse=True)

    return render(request, 'user/transaction_history.html', {
        'records': records,
        'current_type': current_type,
    })


@login_required(login_url='user_login')
def more_services(request):
    return render(request, 'user/more_services.html')


@login_required(login_url='user_login')
def my_team(request):
    profile = get_object_or_404(
        UserProfile.objects.select_related('user', 'vip_level'),
        user=request.user,
    )

    direct_invites = list(
        profile.invited_users.select_related('user', 'vip_level').order_by('-registration_time')
    )

    level_one_ids = [member.id for member in direct_invites]
    level_two_ids = list(
        UserProfile.objects.filter(invited_by_id__in=level_one_ids).values_list('id', flat=True)
    ) if level_one_ids else []
    level_three_ids = list(
        UserProfile.objects.filter(invited_by_id__in=level_two_ids).values_list('id', flat=True)
    ) if level_two_ids else []

    team_profile_ids = level_one_ids + level_two_ids + level_three_ids
    team_user_ids = UserProfile.objects.filter(
        id__in=team_profile_ids
    ).values_list('user_id', flat=True)

    earning_stats = get_user_earning_stats(request.user)
    today_earnings = earning_stats['today_earnings']
    total_earnings = earning_stats['total_earnings']
    order_revenue = earning_stats['order_revenue']

    team_earnings = earning_stats['team_earnings']

    register_url = reverse('user_register')
    invitation_link = request.build_absolute_uri(
        f'{register_url}?invite_code={profile.invite_code}'
    )

    return render(request, 'user/my_team.html', {
        'profile': profile,
        'direct_invites': direct_invites,
        'direct_invite_count': len(direct_invites),
        'team_member_count': len(team_profile_ids),
        'today_earnings': today_earnings,
        'total_earnings': total_earnings,
        'order_revenue': order_revenue,
        'team_earnings': team_earnings,
        'invitation_link': invitation_link,
    })


@login_required(login_url='user_login')
def user_vip_levels(request):
    profile = get_object_or_404(
        UserProfile.objects.select_related('vip_level'),
        user=request.user,
    )
    return render(request, 'user/vip_levels.html', {
        'profile': profile,
        'vip_levels': VipLevel.objects.order_by('id'),
        'home_settings': get_home_settings(request),
    })


@login_required(login_url='user_login')
def user_order_info_page(request, page_key):
    pages = {
        'order_description': (
            'Order Description',
            'order_description_html',
        ),
        'please_note': (
            'Please Note',
            'please_note_html',
        ),
    }

    page = pages.get(page_key)

    if page is None:
        return redirect('user_order')

    page_title, content_field = page
    home_settings = get_home_settings(request)

    return render(request, 'user/content_page.html', {
        'page_title': page_title,
        'page_content': getattr(home_settings, content_field),
        'back_url_name': 'user_order',
    })

@login_required(login_url='user_login')
def verify_withdrawal_password(request):
    if request.method == 'POST':
        password = request.POST.get('transaction_password', '').strip()
        profile = UserProfile.objects.filter(user=request.user).first()

        if profile and check_password(password, profile.transaction_password):
            return JsonResponse({'success': True})

        return JsonResponse({
            'success': False,
            'message': 'Incorrect transaction password.'
        })

    return JsonResponse({'success': False})

def user_logout(request):
    if request.user.is_authenticated:
        profile = UserProfile.objects.filter(user=request.user).first()

        if profile:
            profile.online_status = 'offline'
            profile.save()

    logout(request)

    return redirect('user_login')


@login_required(login_url="user_login")
def user_home(request):
    home_settings = get_home_settings(request)
    announcement_length = len(home_settings.announcement or '')
    marquee_duration = max(30, (announcement_length * 20 + 99) // 100)
    marquee_offset = timezone.now().timestamp() % marquee_duration
    now = timezone.now()
    show_registration_bonus = request.session.pop('show_registration_bonus_popup', False)
    show_campaign = request.session.pop('show_campaign_popup', False)
    last_campaign = request.session.get('campaign_announcement_last_shown')

    if not show_registration_bonus and not show_campaign:
        try:
            show_campaign = now.timestamp() - float(last_campaign) >= 4 * 60 * 60
        except (TypeError, ValueError):
            show_campaign = True

    if show_registration_bonus or show_campaign:
        request.session['campaign_announcement_last_shown'] = now.timestamp()

    return render(
        request,
        "user/home.html",
        {
            "home_settings": home_settings,
            "marquee_duration": marquee_duration,
            "marquee_offset": marquee_offset,
            "show_registration_bonus": show_registration_bonus,
            "show_campaign": show_campaign,
        },
    )

@login_required(login_url='user_login')
def user_withdraw(request):
    profile = get_object_or_404(UserProfile, user=request.user)

    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', '0') or '0')
        wallet_address = request.POST.get('wallet_address', '').strip()
        transaction_password = request.POST.get('transaction_password', '').strip()

        if amount <= 0:
            messages.error(request, 'Invalid withdrawal amount.')
            return redirect('user_withdraw')

        if amount > profile.balance:
            messages.error(request, 'Insufficient balance.')
            return redirect('user_withdraw')

        if profile.vip_level:
            if amount < profile.vip_level.minimum_withdrawal:
                messages.error(request, f'Minimum withdrawal is {profile.vip_level.minimum_withdrawal} USD.')
                return redirect('user_withdraw')

            if amount > profile.vip_level.maximum_withdrawal:
                messages.error(request, f'Maximum withdrawal is {profile.vip_level.maximum_withdrawal} USD.')
                return redirect('user_withdraw')

        if not wallet_address:
            messages.error(request, 'Wallet address is required.')
            return redirect('user_withdraw')

        if not check_password(transaction_password, profile.transaction_password):
            messages.error(request, 'Incorrect withdrawal password.')
            return redirect('user_withdraw')

        profile.balance -= amount
        profile.wallet_address = wallet_address
        profile.save()

        WithdrawalRequest.objects.create(
            user=request.user,
            amount=amount,
            wallet_address=wallet_address,
            status='pending'
        )

        messages.success(request, 'Withdrawal request submitted successfully.')
        return redirect('user_withdraw')

    withdrawals = WithdrawalRequest.objects.filter(user=request.user).order_by('-id')[:10]

    return render(request, 'user/user_partials/withdraw.html', {
        'profile': profile,
        'withdrawals': withdrawals,
        **get_user_earning_stats(request.user),
    })


@login_required(login_url='user_login')
def user_deposit(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    deposits = DepositRecord.objects.filter(
        user=request.user,
        is_hidden_from_user=False,
    ).order_by('-id')[:10]

    return render(request, 'user/user_partials/deposit.html', {
        'profile': profile,
        'deposits': deposits,
        **get_user_earning_stats(request.user),
    })


@login_required(login_url='user_login')
def user_crypto_deposit(request):
    return render(request, 'user/user_partials/crypto_deposit.html')


@login_required(login_url='user_login')
def official_announcement(request):
    return render(request, 'user/official_announcement.html')


@login_required(login_url='user_login')
def user_records(request):
    current_status = request.GET.get("status", "all")

    orders = UserOrder.objects.filter(
        user=request.user,
        is_hidden_from_user=False
    ).select_related(
        "product",
        "lucky_reward"
    ).order_by("-created_at")

    if current_status == "pending":
        orders = orders.filter(status__in=["waiting", "matched"])

    elif current_status == "completed":
        orders = orders.filter(status="completed")

    return render(request, "user/records.html", {
        "orders": orders,
        "current_status": current_status,
    })


@login_required(login_url="user_login")
def user_order(request):
    profile = request.user.userprofile

    active_order = UserOrder.objects.filter(
        user=request.user,
        status="matched"
    ).select_related("product").first()

    completed_orders = UserOrder.objects.filter(
        user=request.user,
        status="completed",
        is_hidden_from_user=False
    ).select_related("product").order_by("-completed_at")[:20]

    remaining_frozen = Decimal("0.00")

    if active_order and active_order.is_successive_order:

        remaining_frozen = (
            active_order.order_price -
            profile.balance
        )

        if remaining_frozen < Decimal("0.00"):
            remaining_frozen = Decimal("0.00")

    latest_lucky_reward = None

    if profile.task_progress > 0:

        latest_lucky_reward = LuckyReward.objects.filter(
            profile=profile,
            status="completed",
            target_order_number__lte=profile.task_progress
        ).order_by(
            "-completed_at",
            "-id"
        ).first()

    return render(
        request,
        "user/order.html",
        {
            "active_order": active_order,
            "completed_orders": completed_orders,
            "remaining_frozen": remaining_frozen,
            "latest_lucky_reward": latest_lucky_reward,
            "home_settings": get_home_settings(request),
            **get_user_earning_stats(request.user),
        }
    )

@staff_required
def staff_reset_user_tasks(request, profile_id):

    profile = get_object_or_404(
        UserProfile,
        id=profile_id
    )

    if request.method == "POST":

        UserOrder.objects.filter(
            user=profile.user,
            status="matched"
        ).update(
            status="cancelled"
        )

        profile.task_progress = 0
        profile.save()

        messages.success(
            request,
            "Task progress reset successfully."
        )

    return staff_user_management_redirect(request)


@login_required(login_url="user_login")
def start_order(request):
    profile = request.user.userprofile

    max_tasks = 0

    if profile.vip_level:
        max_tasks = profile.vip_level.maximum_task

    if max_tasks and profile.task_progress >= max_tasks:
        messages.error(
            request,
            "You have reached your daily task limit."
        )
        return redirect("user_order")

    pending_reward = LuckyReward.objects.filter(
        profile=profile,
        status="pending"
    ).first()

    if pending_reward:
        return redirect(
            "lucky_reward_animation",
            reward_id=pending_reward.id
        )

    active_order = UserOrder.objects.filter(
        user=request.user,
        status="matched"
    ).first()

    if active_order:
        messages.warning(
            request,
            "You have a pending order. Please complete it before starting a new order."
        )
        return redirect("user_order")

    next_order_number = profile.task_progress + 1

    reward = LuckyReward.objects.filter(
        profile=profile,
        target_order_number=next_order_number,
        status="waiting"
    ).first()

    if reward:
        reward.status = "processing"
        reward.save()

        return redirect(
            "lucky_reward_animation",
            reward_id=reward.id
        )

    successive_plan = SuccessiveOrderPlan.objects.filter(
        profile=profile,
        target_order_number=next_order_number,
        status="waiting"
    ).select_related("product").first()

    if successive_plan:
        required_deposit = abs(successive_plan.negative_amount)

        order_price = profile.balance + required_deposit

        commission_rate = Decimal("0")

        if profile.vip_level:
            commission_rate = profile.vip_level.successive_order_commission_rate

        commission = order_price * commission_rate / Decimal("100")

        order = UserOrder.objects.create(
            user=request.user,
            product=successive_plan.product,
            quantity=successive_plan.quantity,
            order_type="successive",
            order_price=order_price,
            commission=commission,
            status="matched",
            is_successive_order=True,
            successive_order_number=next_order_number,
            negative_amount=successive_plan.negative_amount
        )

        successive_plan.status = "matched"
        successive_plan.matched_order = order
        successive_plan.matched_at = timezone.now()
        successive_plan.save()

        return redirect(
            "user_order_detail",
            order_id=order.id
        )

    previously_assigned_product_ids = UserOrder.objects.filter(
        user=request.user,
        product__isnull=False,
    ).values('product_id')

    product = Product.objects.filter(
        price__lt=profile.balance,
    ).exclude(
        id__in=previously_assigned_product_ids,
    ).order_by('-price', 'id').first()

    if not product:
        messages.error(
            request,
            "No new product is available below your current balance."
        )
        return redirect("user_order")

    # Use the closest affordable product once, then fill the remaining balance
    # with whole units of that product without changing successive-order rules.
    quantity = max(1, int(profile.balance // product.price))
    order_price = (product.price * quantity).quantize(Decimal("0.01"))

    commission_rate = Decimal("0")

    if profile.vip_level:
        commission_rate = profile.vip_level.commission_rate

    commission = (order_price * commission_rate / Decimal("100")).quantize(
        Decimal("0.01")
    )

    order = UserOrder.objects.create(
        user=request.user,
        product=product,
        order_type="normal",
        quantity=quantity,
        order_price=order_price,
        commission=commission,
        status="matched"
    )

    return redirect(
        "user_order_detail",
        order_id=order.id
    )


@login_required(login_url="user_login")
def user_order_detail(request, order_id):
    profile = request.user.userprofile

    if user_has_blocking_lucky_reward(profile):
        pending_reward = LuckyReward.objects.filter(
            profile=profile,
            status="pending"
        ).first()

        return redirect(
            "lucky_reward_animation",
            reward_id=pending_reward.id
        )

    order = get_object_or_404(
        UserOrder.objects.select_related("product"),
        id=order_id,
        user=request.user
    )
    unit_price = (
        order.order_price / max(order.quantity, 1)
    ).quantize(Decimal("0.01"))
    reviews = ProductEvaluation.objects.order_by('-created_at')[:10]

    remaining_frozen = Decimal("0.00")
    insufficient_balance = False

    if order.is_successive_order:
        remaining_frozen = order.order_price - profile.balance

        if remaining_frozen < Decimal("0.00"):
            remaining_frozen = Decimal("0.00")

        if remaining_frozen > Decimal("0.00"):
            insufficient_balance = True

    else:
        if profile.balance < order.order_price:
            insufficient_balance = True

    return render(request, "user/order_detail.html", {
        "order": order,
        "unit_price": unit_price,
        "profile": profile,
        "reviews": reviews,
        "remaining_frozen": remaining_frozen,
        "insufficient_balance": insufficient_balance,
    })


@login_required(login_url="user_login")
def submit_order(request, order_id):
    profile = request.user.userprofile

    if user_has_blocking_lucky_reward(profile):
        pending_reward = LuckyReward.objects.filter(
            profile=profile,
            status="pending"
        ).first()

        return redirect(
            "lucky_reward_animation",
            reward_id=pending_reward.id
        )

    if request.method != "POST":
        return redirect("user_order_detail", order_id=order_id)

    with transaction.atomic():
        profile = get_object_or_404(
            UserProfile.objects.select_for_update().select_related('invited_by'),
            user=request.user,
        )
        order = get_object_or_404(
            UserOrder.objects.select_for_update(),
            id=order_id,
            user=request.user,
            status="matched",
        )

        if profile.balance < order.order_price:
            remaining_topup = order.order_price - profile.balance
            messages.error(
                request,
                f"Insufficient balance. Please top up {remaining_topup} USD."
            )
            return redirect("user_order_detail", order_id=order.id)

        rating = int(request.POST.get("rating", 5))
        rating = max(1, min(rating, 5))
        comment = request.POST.get("comment", "").strip()

        order.rating = rating
        order.comment = comment
        order.status = "completed"
        order.completed_at = timezone.now()
        order.save(update_fields=['rating', 'comment', 'status', 'completed_at'])

        profile.balance += order.commission
        profile.task_progress += 1
        profile.save(update_fields=['balance', 'task_progress'])

        inviter = profile.invited_by
        if inviter:
            referral_amount = (
                order.commission * Decimal('20.00') / Decimal('100.00')
            ).quantize(Decimal('0.01'))
            inviter = UserProfile.objects.select_for_update().get(pk=inviter.pk)
            ReferralCommission.objects.create(
                inviter=inviter,
                invitee=profile,
                order=order,
                amount=referral_amount,
            )
            inviter.balance += referral_amount
            inviter.save(update_fields=['balance'])

    messages.success(request, "Order submitted successfully.")
    return redirect("user_order")

@login_required(login_url='user_login')
def user_messages(request):
    notifications = []

    notifications.extend({
        'id': item.id,
        'type': 'deposit',
        'title': 'Registration bonus' if item.remark == 'Registration bonus' else 'Deposit credited',
        'amount': item.amount,
        'status': 'Success',
        'created_at': item.created_at,
        'transaction_id': item.transaction_id,
        'is_read': item.is_read_by_user,
    } for item in DepositRecord.objects.filter(user=request.user, is_hidden_from_user=False))

    withdrawal_titles = {
        'approved': 'Withdrawal successful',
        'pending': 'Withdrawal pending',
        'rejected': 'Withdrawal rejected',
    }

    withdrawal_statuses = {
        'approved': 'Success',
        'pending': 'Pending',
        'rejected': 'Rejected',
    }

    notifications.extend({
        'id': item.id,
        'type': 'withdrawal',
        'title': withdrawal_titles.get(item.status, 'Withdrawal updated'),
        'amount': item.amount,
        'status': withdrawal_statuses.get(item.status, item.status.title()),
        'created_at': item.created_at,
        'transaction_id': item.transaction_id,
        'is_read': item.is_read_by_user,
    } for item in WithdrawalRequest.objects.filter(user=request.user))

    notifications.sort(key=lambda item: item['created_at'], reverse=True)

    return render(request, 'user/messages.html', {
        'notifications': notifications[:20],
    })


@login_required(login_url='user_login')
def user_unread_count(request):
    support_count = SupportMessage.objects.filter(
        user=request.user,
        is_read_by_user=False,
    ).count()
    system_count = (
        DepositRecord.objects.filter(
            user=request.user,
            is_read_by_user=False,
            is_hidden_from_user=False,
        ).count()
        + WithdrawalRequest.objects.filter(user=request.user, is_read_by_user=False).count()
    )
    return JsonResponse({
        'count': support_count + system_count,
        'support_count': support_count,
        'system_count': system_count,
    })


def user_support_poll(request):
    if request.user.is_authenticated:
        support_user = request.user
    else:
        guest_user_id = request.session.get('guest_support_user_id')
        support_user = User.objects.filter(id=guest_user_id, username__startswith='guest-').first()
        if support_user is None:
            return JsonResponse({'messages': []})

    try:
        message_id = max(0, int(request.GET.get('after', 0)))
    except (TypeError, ValueError):
        message_id = 0
    return JsonResponse({'messages': support_messages_after(support_user, message_id)})


@staff_required
def staff_support_poll(request, user_id):
    user = get_object_or_404(User, id=user_id)
    try:
        message_id = max(0, int(request.GET.get('after', 0)))
    except (TypeError, ValueError):
        message_id = 0
    return JsonResponse({'messages': support_messages_after(user, message_id)})


@staff_required
def staff_unread_support_count(request):
    count = SupportMessage.objects.filter(
        sender__is_staff=False,
        is_read_by_staff=False,
    ).count()
    return JsonResponse({'count': count})


@login_required(login_url='user_login')
def user_transaction_notification(request, transaction_type, record_id):
    if transaction_type == 'deposit':
        record = get_object_or_404(DepositRecord, id=record_id, user=request.user)
    elif transaction_type == 'withdrawal':
        record = get_object_or_404(WithdrawalRequest, id=record_id, user=request.user)
    else:
        return redirect('user_messages')

    if not record.is_read_by_user:
        record.is_read_by_user = True
        record.save(update_fields=['is_read_by_user'])

    history_url = reverse('transaction_notice')
    return redirect(f'{history_url}?type={transaction_type}')


@login_required(login_url='user_login')
def user_settings(request):
    profile = request.user.userprofile

    latest_lucky_reward = None

    if profile.task_progress > 0:
        latest_lucky_reward = LuckyReward.objects.filter(
            profile=profile,
            status="completed",
            target_order_number__lte=profile.task_progress
        ).order_by(
            "-completed_at",
            "-id"
        ).first()

    return render(request, 'user/settings.html', {
        'latest_lucky_reward': latest_lucky_reward,
        **get_user_earning_stats(request.user),
    })

@login_required(login_url='user_login')
def user_trading_account(request):
    profile = get_object_or_404(UserProfile, user=request.user)

    if request.method == 'POST':
        wallet_address = request.POST.get('wallet_address', '').strip()

        if not wallet_address:
            messages.error(request, 'Wallet address is required.')
            return redirect('user_trading_account')

        profile.wallet_address = wallet_address
        profile.save()

        messages.success(request, 'Wallet address saved successfully.')
        return redirect('user_trading_account')

    return render(request, 'user/user_partials/trading_account.html', {
        'profile': profile
    })


@login_required(login_url='user_login')
def user_edit_wallet_address(request):
    profile = get_object_or_404(UserProfile, user=request.user)

    if request.method == 'POST':
        wallet_address = request.POST.get('wallet_address', '').strip()

        if not wallet_address:
            messages.error(request, 'Wallet address is required.')
            return redirect('user_edit_wallet_address')

        profile.wallet_address = wallet_address
        profile.save(update_fields=['wallet_address'])
        messages.success(request, 'Wallet address updated successfully.')
        return redirect('user_edit_wallet_address')

    return render(request, 'user/user_partials/edit_wallet_address.html', {
        'profile': profile,
    })

@login_required(login_url='user_login')
def user_personal_information(request):
    profile = request.user.userprofile
    return render(request, 'user/user_partials/personal_information.html', {'profile': profile})

@login_required(login_url='user_login')
def user_update_email(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        request.user.email = email
        request.user.save()
        messages.success(request, 'Email updated successfully.')
        return redirect('user_personal_information')

    return render(request, 'user/user_partials/update_email.html')


@login_required(login_url='user_login')
def user_update_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()

        if not request.user.check_password(old_password):
            messages.error(request, 'Old password is incorrect.')
            return redirect('user_update_password')

        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)

        messages.success(request, 'Login password updated successfully.')
        return redirect('user_personal_information')

    return render(request, 'user/user_partials/update_password.html')


@login_required(login_url='user_login')
def user_update_transaction_password(request):
    profile = request.user.userprofile

    if request.method == 'POST':
        old_password = request.POST.get('old_transaction_password', '').strip()
        new_password = request.POST.get('new_transaction_password', '').strip()

        if not check_password(old_password, profile.transaction_password):
            messages.error(request, 'Old transaction password is incorrect.')
            return redirect('user_update_transaction_password')

        profile.transaction_password = make_password(new_password)
        profile.save()

        messages.success(request, 'Transaction password updated successfully.')
        return redirect('user_personal_information')

    return render(request, 'user/user_partials/update_transaction_password.html')

def customer_service(request):
    support_user = request.user
    is_guest = not request.user.is_authenticated
    if is_guest:
        guest_user_id = request.session.get('guest_support_user_id')
        support_user = User.objects.filter(id=guest_user_id, username__startswith='guest-').first()
        if support_user is None:
            support_user = User.objects.create_user(
                username=f'guest-{uuid4().hex[:20]}',
                password=None,
            )
            support_user.set_unusable_password()
            support_user.save(update_fields=['password'])
            request.session['guest_support_user_id'] = support_user.id

    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        image = request.FILES.get('image')

        if image:
            allowed_image_types = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}

            if image.content_type not in allowed_image_types:
                messages.error(request, 'Please select a JPG, PNG, WEBP, or GIF image.')
                return redirect(f"{reverse('customer_service')}?sent=1")

            if image.size > 5 * 1024 * 1024:
                messages.error(request, 'Image must be 5 MB or smaller.')
                return redirect(f"{reverse('customer_service')}?sent=1")

        if message or image:
            support_message = SupportMessage.objects.create(
                user=support_user,
                sender=support_user,
                message=message,
                image=image,
                message_type='image' if image else 'text',
                is_read_by_user=True,
                is_read_by_staff=False
            )
            broadcast_support_message(support_message)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': True, **support_message_payload(support_message)})

        return redirect(f"{reverse('customer_service')}?sent=1")

    messages_list = SupportMessage.objects.filter(
        user=support_user
    ).order_by('created_at')

    SupportMessage.objects.filter(
        user=support_user,
        sender__is_staff=True,
        is_read_by_user=False
    ).update(is_read_by_user=True)

    return render(request, 'user/customer_service.html', {
        'messages_list': messages_list,
        'show_support_card': request.GET.get('sent') != '1',
        'support_user': support_user,
        'is_guest': is_guest,
    })
