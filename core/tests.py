from unittest.mock import patch

from django.core.cache import cache
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import (
    DepositRecord,
    HomePageSettings,
    Product,
    SupportMessage,
    UserOrder,
    WithdrawalRequest,
)
from .views import get_random_product


class HomePageSettingsCacheTests(TestCase):
    def setUp(self):
        cache.clear()
        HomePageSettings.objects.create(pk=1, brand_name="Initial")
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_load_uses_cache_after_first_database_read(self):
        with self.assertNumQueries(1):
            first = HomePageSettings.load()

        with self.assertNumQueries(0):
            second = HomePageSettings.load()

        self.assertEqual(first.pk, second.pk)

    def test_save_invalidates_cached_settings(self):
        settings = HomePageSettings.load()
        settings.brand_name = "Updated"
        settings.save()

        with self.assertNumQueries(1):
            refreshed = HomePageSettings.load()

        self.assertEqual(refreshed.brand_name, "Updated")


class RandomProductTests(TestCase):
    def test_returns_none_without_products(self):
        self.assertIsNone(get_random_product())

    def test_selects_product_without_random_database_sort(self):
        first = Product.objects.create(product_id=10001, name="First")
        second = Product.objects.create(product_id=10002, name="Second")

        with patch("core.views.random.randint", return_value=first.id + 1):
            selected = get_random_product()

        self.assertEqual(selected, second)


class CustomerEntryAndWalletTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="customer", password="test-password")
        self.client.force_login(self.user)

    def test_site_root_redirects_to_customer_login(self):
        response = self.client.get(reverse("site_root"))
        self.assertRedirects(response, reverse("user_login"), fetch_redirect_response=False)


    def test_customer_pages_include_navigation_loader(self):
        response = self.client.get(reverse("user_home"))
        self.assertContains(response, 'id="pageLoadingOverlay"')

    def test_login_page_includes_navigation_loader(self):
        self.client.logout()
        response = self.client.get(reverse("user_login"))
        self.assertContains(response, 'id="pageLoadingOverlay"')

    def test_messages_navigation_shows_combined_unread_count(self):
        staff = User.objects.create_user(username="support", password="test-password", is_staff=True)
        SupportMessage.objects.create(
            user=self.user,
            sender=staff,
            message="Support reply",
            is_read_by_user=False,
            is_read_by_staff=True,
        )
        DepositRecord.objects.create(user=self.user, amount="25.00", is_read_by_user=False)
        WithdrawalRequest.objects.create(user=self.user, amount="10.00", is_read_by_user=False)

        response = self.client.get(reverse("user_home"))

        self.assertContains(response, 'class="message-count-badge"')
        self.assertContains(response, "3 unread messages")

        messages_response = self.client.get(reverse("user_messages"))
        self.assertContains(messages_response, 'class="service-unread-badge"')
        self.assertContains(messages_response, "1 unread customer service message")

    def test_messages_navigation_hides_badge_without_unread_messages(self):
        response = self.client.get(reverse("user_home"))
        self.assertNotContains(response, 'class="message-count-badge"')

    def test_verify_button_is_hidden_when_authorization_is_disabled(self):
        profile = self.user.userprofile
        profile.need_authorization = False
        profile.save(update_fields=["need_authorization"])
        response = self.client.get(reverse("user_edit_wallet_address"))
        self.assertNotContains(response, 'id="connectCryptoWallet"')
        self.assertNotContains(response, "wallet-connect.js")

    def test_verify_button_is_shown_when_authorization_is_enabled(self):
        profile = self.user.userprofile
        profile.need_authorization = True
        profile.save(update_fields=["need_authorization"])
        response = self.client.get(reverse("user_edit_wallet_address"))
        self.assertContains(response, 'id="connectCryptoWallet"')
        self.assertContains(response, "Verify")
        self.assertContains(response, "wallet-connect.js")


class NormalOrderQuantityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="order-customer", password="test-password")
        self.client.force_login(self.user)
        self.profile = self.user.userprofile
        self.profile.balance = "1000.00"
        self.profile.save(update_fields=["balance"])

    def test_normal_order_uses_whole_affordable_quantity(self):
        Product.objects.create(product_id=10011, name="Expensive", price="1200.00")
        product = Product.objects.create(product_id=10012, name="Closest", price="240.00")
        Product.objects.create(product_id=10013, name="Cheap", price="100.00")

        response = self.client.get(reverse("start_order"))

        self.assertEqual(response.status_code, 302)
        order = UserOrder.objects.get(user=self.user)
        self.assertEqual(order.product, product)
        self.assertEqual(order.quantity, 4)
        self.assertEqual(order.order_price, 960)

    def test_normal_order_does_not_reuse_a_product(self):
        product = Product.objects.create(product_id=10014, name="Only product", price="240.00")
        UserOrder.objects.create(
            user=self.user,
            product=product,
            quantity=1,
            order_type="normal",
            order_price="240.00",
            commission="0.00",
            status="completed",
        )

        response = self.client.get(reverse("start_order"))

        self.assertRedirects(response, reverse("user_order"))
        self.assertEqual(UserOrder.objects.filter(user=self.user).count(), 1)


class AZTokenDeployerAccessTests(TestCase):
    def test_deployer_page_requires_staff_login(self):
        response = self.client.get(reverse("staff_aztoken_deployer"))

        self.assertRedirects(response, reverse("staff_login"), fetch_redirect_response=False)

    def test_deployer_page_is_available_to_staff(self):
        staff = User.objects.create_user(
            username="token-admin",
            password="test-password",
            is_staff=True,
        )
        self.client.force_login(staff)

        response = self.client.get(reverse("staff_aztoken_deployer"))

        self.assertContains(response, "Deploy AZToken to Sepolia")
        self.assertContains(response, "11155111")
        self.assertContains(response, "aztoken-deployer.js")
