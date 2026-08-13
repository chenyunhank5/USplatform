from unittest.mock import patch

from django.core.cache import cache
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import HomePageSettings, Product
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
