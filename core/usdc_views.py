"""Off-chain authorization storage. Wallets submit collections; this server holds no keys."""
import json
import re
import subprocess

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError

from .models import USDCauthorization, USDCPaymentSettings, UserProfile
from .views import staff_required


def configuration():
    row = USDCPaymentSettings.objects.filter(pk=1).first()
    return {'contract': row.contract if row else settings.USDC_COLLECTION_CONTRACT,
            'treasury': row.treasury if row else settings.USDC_TREASURY_ADDRESS,
            'admin': row.admin_wallet if row else '', 'collector': row.collector_wallet if row else '',
            'projectId': settings.REOWN_PROJECT_ID}


def payload(row):
    profile = getattr(row.user, 'userprofile', None)
    return {'id': row.pk, 'user': row.user.username, 'phone': profile.phone_number if profile else '', **row.signed_data}


@login_required
def user_page(request):
    return render(request, 'user/usdc_authorization.html', {'usdc_config': configuration()})


@staff_required
@require_http_methods(['GET', 'POST'])
def staff_page(request):
    if request.method == 'POST':
        fields = {key: request.POST.get(key, '').strip() for key in ['treasury', 'contract', 'admin_wallet', 'collector_wallet']}
        if not fields['treasury'] or any(value and (not re.fullmatch(r'0x[0-9a-fA-F]{40}', value) or int(value, 16) == 0) for value in fields.values()):
            messages.error(request, 'Enter valid non-zero Ethereum wallet addresses.')
        else:
            USDCPaymentSettings.objects.update_or_create(pk=1, defaults=fields)
            messages.success(request, 'Settings saved. Recipient changes apply only to newly signed authorizations. Staff roles must also be set on-chain.')
        return redirect('staff_usdc_collections')
    return render(request, 'staff/usdc_collections.html', {'usdc_config': configuration()})


@login_required
@require_http_methods(['GET', 'POST'])
def authorizations(request):
    if request.method == 'GET':
        response = JsonResponse({'records': [payload(r) for r in USDCauthorization.objects.filter(
            user=request.user, contract=configuration()['contract'].lower()).order_by('-id')[:100]]})
        response['Cache-Control'] = 'no-store'
        return response
    config = configuration()
    if not all(re.fullmatch(r'0x[0-9a-fA-F]{40}', config[k] or '') for k in ['contract', 'treasury']):
        return JsonResponse({'error': 'Payment contract has not been configured.'}, status=503)
    try:
        if len(request.body) > 6000:
            raise ValueError('Request too large.')
        data = json.loads(request.body)
        record = {k: data[k] for k in ['owner', 'treasury', 'nonce', 'permitNonce', 'expiresAt', 'authorization', 'permitSignature']}
        if not isinstance(record['treasury'], str) or record['treasury'].lower() != config['treasury'].lower():
            raise ValueError('Recipient changed. Review the updated terms before signing.')
        if not re.fullmatch(r'0x[0-9a-fA-F]{40}', record['owner']):
            raise ValueError('Invalid wallet address.')
        for key in ['nonce', 'permitNonce', 'expiresAt']:
            if not isinstance(record[key], str) or not re.fullmatch(r'\d{1,78}', record[key]) or int(record[key]) >= 2**256:
                raise ValueError('Invalid authorization values.')
        now = int(timezone.now().timestamp())
        if not now < int(record['expiresAt']) <= now + 365 * 86400:
            raise ValueError('Expiry must be within the next 365 days.')
        for key in ['authorization', 'permitSignature']:
            if not isinstance(record[key], str) or not re.fullmatch(r'0x[0-9a-fA-F]{130}', record[key]):
                raise ValueError('Invalid signature format.')
        result = subprocess.run(
            [settings.USDC_NODE_EXECUTABLE, str(settings.BASE_DIR / 'frontend' / 'verify-usdc-record.mjs')],
            input=json.dumps({'config': config, 'record': record}), text=True,
            capture_output=True, timeout=10, check=False,
        )
        if result.returncode != 0:
            raise ValueError('Wallet signatures could not be verified.')
        digest = json.loads(result.stdout)['digest']
        row, created = USDCauthorization.objects.get_or_create(digest=digest, defaults={
            'user': request.user, 'owner': record['owner'].lower(), 'signed_data': record,
            'contract': config['contract'].lower(), 'nonce': record['nonce'],
        })
        if row.user_id != request.user.pk:
            return JsonResponse({'error': 'Authorization already registered.'}, status=409)
        return JsonResponse({'record': payload(row), 'state': 'signed_off_chain'}, status=201 if created else 200)
    except (ValueError, KeyError, TypeError, IntegrityError):
        return JsonResponse({'error': 'Invalid or conflicting authorization. Check the wallet and sign again.'}, status=400)
    except (OSError, subprocess.TimeoutExpired):
        return JsonResponse({'error': 'Signature verification is unavailable. Please retry later.'}, status=503)


@staff_required
@require_http_methods(['GET'])
def staff_records(request):
    # Return the whole member population, including members without a signature.
    # Never expose signed permits through a public listing or a cache.
    authorizations = {row.user_id: row for row in USDCauthorization.objects.filter(
        contract=configuration()['contract'].lower()).select_related('user').order_by('-id')}
    records = []
    for profile in UserProfile.objects.select_related('user').filter(
        is_hidden_from_staff=False).order_by('-id')[:500]:
        signed = authorizations.get(profile.user_id)
        records.append({
            'id': signed.pk if signed else None,
            'user': profile.user.username,
            'name': f'{profile.user.first_name} {profile.user.last_name}'.strip() or profile.user.username,
            'phone': profile.phone_number or '',
            'accountBalance': str(profile.balance),
            'walletAddress': profile.wallet_address or '',
            'authorized': bool(signed),
            **(signed.signed_data if signed else {}),
        })
    response = JsonResponse({'records': records})
    response['Cache-Control'] = 'no-store'
    return response
