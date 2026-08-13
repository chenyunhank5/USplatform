from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase

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
