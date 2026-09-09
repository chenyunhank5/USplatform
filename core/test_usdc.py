import json
import subprocess
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from .models import USDCPaymentSettings, USDCauthorization


@override_settings(SECURE_SSL_REDIRECT=False, ALLOWED_HOSTS=['testserver'],
                   CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class USDCPaymentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='payer')
        cls.other = User.objects.create_user(username='other')
        cls.staff = User.objects.create_user(username='collector', is_staff=True)
        cls.config = {'contract': '0x1111111111111111111111111111111111111111',
                      'treasury': '0x2222222222222222222222222222222222222222'}
        USDCPaymentSettings.objects.create(pk=1, **cls.config)
        script = """
import {Wallet} from 'ethers';
import {messages,permitTypes,termsTypes} from './frontend/usdc-protocol.mjs';
const wallet=Wallet.createRandom();
const config=JSON.parse(process.argv[1]);
const record={owner:wallet.address,treasury:config.treasury,nonce:'0',permitNonce:'0',expiresAt:String(Math.floor(Date.now()/1000)+3600)};
const m=messages(config,record);
record.authorization=await wallet.signTypedData(m.termsDomain,termsTypes,m.terms);
record.permitSignature=await wallet.signTypedData(m.permitDomain,permitTypes,m.permit);
process.stdout.write(JSON.stringify(record));
"""
        result = subprocess.run(['node', '--input-type=module', '-e', script, json.dumps(cls.config)],
                                cwd=settings.BASE_DIR, capture_output=True, text=True, check=True)
        cls.record = json.loads(result.stdout)

    def post_record(self, record=None):
        return self.client.post(reverse('user_usdc_records'), json.dumps(record or self.record), content_type='application/json')

    def test_verified_signature_saved_off_chain_and_idempotent(self):
        self.client.force_login(self.user)
        response = self.post_record()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['state'], 'signed_off_chain')
        self.assertEqual(self.post_record().status_code, 200)
        self.assertEqual(USDCauthorization.objects.count(), 1)

    def test_tampered_signatures_and_expiry_rejected(self):
        self.client.force_login(self.user)
        for changes in [{'nonce': '1'}, {'permitNonce': '1'}, {'expiresAt': '1'},
                        {'authorization': '0x' + '00' * 65}, {'treasury': []}]:
            self.assertEqual(self.post_record({**self.record, **changes}).status_code, 400)
        self.assertEqual(USDCauthorization.objects.count(), 0)

    def test_record_is_private_and_cannot_be_claimed_by_another_user(self):
        self.client.force_login(self.user)
        self.post_record()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('user_usdc_records')).json()['records'], [])
        self.assertEqual(self.post_record().status_code, 409)
        self.assertEqual(self.client.get(reverse('staff_usdc_records')).status_code, 302)
        self.client.force_login(self.staff)
        response = self.client.get(reverse('staff_usdc_records'))
        self.assertEqual(len(response.json()['records']), 1)
        self.assertEqual(response['Cache-Control'], 'no-store')

    def test_staff_recipient_change_does_not_modify_existing_signed_terms(self):
        self.client.force_login(self.user)
        self.post_record()
        self.client.force_login(self.staff)
        response = self.client.post(reverse('staff_usdc_collections'), {
            **self.config, 'treasury': '0x3333333333333333333333333333333333333333'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(USDCauthorization.objects.get().signed_data['treasury'], self.config['treasury'])
        self.client.force_login(self.other)
        self.assertEqual(self.post_record().status_code, 400)

    def test_pages_render_and_old_trading_route_redirects(self):
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse('user_usdc_authorization')), 'Sign 100 USDC authorization')
        self.assertRedirects(self.client.get(reverse('user_trading_account')), reverse('user_usdc_authorization'))
        self.client.force_login(self.staff)
        self.assertContains(self.client.get(reverse('staff_usdc_collections')), 'Payment wallet settings')
        self.assertRedirects(self.client.get(reverse('staff_aztoken_deployer')), reverse('staff_usdc_collections'))

    def test_settings_requires_staff_and_post_requires_csrf(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(reverse('staff_usdc_collections'), self.config).status_code, 302)
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(reverse('user_usdc_records'), json.dumps(self.record), content_type='application/json').status_code, 403)
