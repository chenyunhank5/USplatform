from decimal import Decimal
from datetime import timedelta

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q, Max

from .models import UserProfile, VipLevel, Product, ProductEvaluation, WithdrawalRequest, SupportMessage, UserOrder, LuckyReward


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    return ip


def staff_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('staff_login')

        if not request.user.is_staff:
            return redirect('user_home')

        return view_func(request, *args, **kwargs)

    return wrapper


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

@staff_required
def staff_user_management(request):
    profiles = UserProfile.objects.select_related(
        'user',
        'invited_by',
        'invited_by__user',
        'vip_level'
    ).all().order_by('-id')

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
            return redirect('staff_user_management')

        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('staff_user_management')

        invited_by_profile = None

        if upper_level_id:
            invited_by_profile = UserProfile.objects.filter(id=upper_level_id).first()

            if not invited_by_profile:
                messages.error(request, 'Upper level ID does not exist.')
                return redirect('staff_user_management')

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

    return redirect('staff_user_management')


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
            return redirect('staff_user_management')

        if User.objects.filter(username__iexact=username).exclude(id=profile.user.id).exists():
            messages.error(request, 'Username already exists.')
            return redirect('staff_user_management')

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

    return redirect('staff_user_management')


@staff_required
def staff_score_modify(request, profile_id):
    profile = get_object_or_404(UserProfile, id=profile_id)

    if request.method == 'POST':
        operation_type = request.POST.get('operation_type')
        amount = Decimal(request.POST.get('amount', '0'))

        if amount <= 0:
            messages.error(request, 'Amount must be greater than 0.')
            return redirect('staff_user_management')

        if operation_type == 'plus':
            profile.balance += amount

        elif operation_type == 'minus':
            if profile.balance < amount:
                messages.error(request, 'Insufficient balance.')
                return redirect('staff_user_management')

            profile.balance -= amount

        profile.save()

        messages.success(request, 'Balance updated successfully.')

    return redirect('staff_user_management')


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

    return redirect('staff_user_management')


@staff_required
def staff_update_withdrawal_password(request, profile_id):
    profile = get_object_or_404(UserProfile, id=profile_id)

    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()

        if new_password:
            profile.transaction_password = make_password(new_password)
            profile.save()
            messages.success(request, 'Withdrawal password updated successfully.')

    return redirect('staff_user_management')


@staff_required
def staff_update_wallet_address(request, profile_id):
    profile = get_object_or_404(UserProfile, id=profile_id)

    if request.method == 'POST':
        wallet_address = request.POST.get('wallet_address', '').strip()

        profile.wallet_address = wallet_address
        profile.save()

        messages.success(request, 'Wallet address updated successfully.')

    return redirect('staff_user_management')


@staff_required
def staff_successive_order_page(request, profile_id):
    profile = get_object_or_404(UserProfile, id=profile_id)

    orders = UserOrder.objects.filter(
        user=profile.user,
        is_successive_order=True
    ).select_related("product").order_by("successive_order_number")

    missions = Product.objects.all().order_by("-id")

    return render(request, "staff/successive_order_page.html", {
        "profile": profile,
        "orders": orders,
        "missions": missions,
    })

@staff_required
def staff_add_successive_order(request):

    if request.method == 'POST':

        profile_id = request.POST.get('profile_id')

        mission_id = request.POST.get('mission_id')

        target_turn = request.POST.get('target_turn')

        negative_amount = request.POST.get('negative_amount')

        profile = get_object_or_404(
            UserProfile,
            id=profile_id
        )

        product = get_object_or_404(
            Product,
            id=mission_id
        )

        commission_rate = Decimal("0")

        if profile.vip_level:
            commission_rate = (
                profile.vip_level.successive_order_commission_rate
            )

        commission = (
            product.price
            * commission_rate
            / Decimal("100")
        )

        UserOrder.objects.create(
            user=profile.user,
            product=product,
            order_price=product.price,
            commission=commission,
            status='waiting',
            is_successive_order=True,
            successive_order_number=int(target_turn),
            negative_amount=Decimal(negative_amount)
        )

        return redirect(
            'staff_successive_order_page',
            profile.id
        )

    return redirect('staff_user_management')

@staff_required
def staff_edit_successive_order_frozen(request, order_id):

    order = get_object_or_404(
        UserOrder,
        id=order_id,
        is_successive_order=True
    )

    profile = get_object_or_404(
        UserProfile,
        user=order.user
    )

    if request.method == "POST":

        if order.status != "waiting":
            return redirect(
                "staff_successive_order_page",
                profile_id=profile.id
            )

        frozen_amount = request.POST.get("negative_amount") or "0"

        order.negative_amount = Decimal(frozen_amount)
        order.save()

        return redirect(
            "staff_successive_order_page",
            profile_id=profile.id
        )

    return redirect(
        "staff_successive_order_page",
        profile_id=profile.id
    )

@staff_required
def staff_delete_successive_order(request, order_id):

    order = get_object_or_404(
        UserOrder,
        id=order_id,
        is_successive_order=True
    )

    profile = get_object_or_404(
        UserProfile,
        user=order.user
    )

    if request.method == "POST":

        order.delete()

        return redirect(
            "staff_successive_order_page",
            profile_id=profile.id
        )

    return redirect(
        "staff_successive_order_page",
        profile_id=profile.id
    )

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

    return redirect("staff_user_management")

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

    return render(request, 'staff/product_list.html', {
        'products': products
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
                SupportMessage.objects.create(
                    user=selected_user,
                    sender=request.user,
                    message=message,
                    image=image,
                    message_type='image' if image else 'text',
                    is_read_by_staff=True,
                    is_read_by_user=False
                )

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
        profile.ip_address = get_client_ip(request)
        profile.vip_level = vip1
        profile.save()

        login(request, user)

        messages.success(request, 'Registration successful.')

        return redirect('user_home')

    return render(request, 'user/register.html')


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)

            profile = UserProfile.objects.filter(user=user).first()

            if profile:
                profile.ip_address = get_client_ip(request)
                profile.online_status = 'online'
                profile.recent_login = timezone.now()
                profile.save()

            return redirect('user_home')

        messages.error(request, 'Invalid username or password.')
        return redirect('user_login')

    return render(request, 'user/login.html')

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


@login_required(login_url='user_login')
def user_home(request):
    return render(request, 'user/home.html')

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
    })


@login_required(login_url='user_login')
def user_records(request):
    withdrawals = WithdrawalRequest.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, 'user/records.html', {
        'withdrawals': withdrawals
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
        status="completed"
    ).select_related("product").order_by("-completed_at")[:20]

    remaining_frozen = Decimal("0.00")

    if active_order and active_order.is_successive_order:
        remaining_frozen = active_order.order_price - profile.balance

        if remaining_frozen < Decimal("0.00"):
            remaining_frozen = Decimal("0.00")

    return render(request, "user/order.html", {
        "active_order": active_order,
        "completed_orders": completed_orders,
        "remaining_frozen": remaining_frozen,
    })



@login_required(login_url="user_login")
def start_order(request):
    profile = request.user.userprofile

    pending_reward = LuckyReward.objects.filter(
        profile=profile,
        status="pending"
    ).first()

    if pending_reward:
        return redirect("lucky_reward_animation", reward_id=pending_reward.id)

    active_order = UserOrder.objects.filter(
        user=request.user,
        status="matched"
    ).first()

    if active_order:
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
        return redirect("lucky_reward_animation", reward_id=reward.id)

    product = Product.objects.order_by("?").first()

    if not product:
        messages.error(request, "No product found.")
        return redirect("user_order")

    commission_rate = Decimal("0")

    if profile.vip_level:
        commission_rate = profile.vip_level.commission_rate

    commission = product.price * commission_rate / Decimal("100")

    UserOrder.objects.create(
        user=request.user,
        product=product,
        order_type="normal",
        order_price=product.price,
        commission=commission,
        status="matched"
    )

    return redirect("user_order")

@login_required(login_url="user_login")
def user_order_detail(request, order_id):

    profile = request.user.userprofile

    if user_has_blocking_lucky_reward(profile):
        pending_reward = LuckyReward.objects.filter(profile=profile, status="pending").first()
        return redirect("lucky_reward_animation", reward_id=pending_reward.id)

    order = get_object_or_404(
        UserOrder.objects.select_related("product"),
        id=order_id,
        user=request.user
    )

    profile = request.user.userprofile

    remaining_frozen = Decimal("0.00")
    insufficient_balance = False

    if order.is_successive_order:

        remaining_frozen = (
            abs(order.negative_amount)
            - profile.balance
        )

        if remaining_frozen < Decimal("0.00"):
            remaining_frozen = Decimal("0.00")

        if remaining_frozen > Decimal("0.00"):
            insufficient_balance = True

    else:

        if profile.balance < order.order_price:
            insufficient_balance = True

    return render(request, "user/order_detail.html", {
        "order": order,
        "profile": profile,
        "remaining_frozen": remaining_frozen,
        "insufficient_balance": insufficient_balance,
    })


@login_required(login_url="user_login")
def submit_order(request, order_id):
    profile = request.user.userprofile

    if user_has_blocking_lucky_reward(profile):
        pending_reward = LuckyReward.objects.filter(profile=profile, status="pending").first()
        return redirect("lucky_reward_animation", reward_id=pending_reward.id)

    order = get_object_or_404(
        UserOrder,
        id=order_id,
        user=request.user,
        status="matched"
    )

    profile = request.user.userprofile

    if request.method == "POST":
        if profile.balance < order.order_price:
            remaining_topup = order.order_price - profile.balance

            messages.error(
                request,
                f"Insufficient balance. Please top up {remaining_topup} USD."
            )

            return redirect("user_order_detail", order_id=order.id)

        rating = int(request.POST.get("rating", 5))
        comment = request.POST.get("comment", "").strip()

        order.rating = rating
        order.comment = comment
        order.status = "completed"
        order.completed_at = timezone.now()
        order.save()

        profile.balance += order.commission
        profile.task_progress += 1
        profile.save()

        messages.success(request, "Order submitted successfully.")
        return redirect("user_order")

    return redirect("user_order_detail", order_id=order.id)

@login_required(login_url='user_login')
def user_messages(request):
    return render(request, 'user/messages.html')


@login_required(login_url='user_login')
def user_settings(request):
    return render(request, 'user/settings.html')

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

@login_required(login_url='user_login')
def customer_service(request):

    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        image = request.FILES.get('image')

        if message or image:
            SupportMessage.objects.create(
                user=request.user,
                sender=request.user,
                message=message,
                image=image,
                message_type='image' if image else 'text',
                is_read_by_user=True,
                is_read_by_staff=False
            )

        return redirect('customer_service')

    messages_list = SupportMessage.objects.filter(
        user=request.user
    ).order_by('created_at')

    SupportMessage.objects.filter(
        user=request.user,
        sender__is_staff=True,
        is_read_by_user=False
    ).update(is_read_by_user=True)

    return render(request, 'user/customer_service.html', {
        'messages_list': messages_list
    })
