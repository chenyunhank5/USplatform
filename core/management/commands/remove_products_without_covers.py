import json
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core.models import Product


class Command(BaseCommand):
    help = 'Preview or remove products without cover images within a selected import window.'

    def add_arguments(self, parser):
        parser.add_argument('--after', required=True, help='ISO timestamp, for example 2026-09-06T15:30:00+00:00')
        parser.add_argument('--before', required=True, help='ISO timestamp, for example 2026-09-06T16:00:00+00:00')
        parser.add_argument('--min-price', type=float, default=1500)
        parser.add_argument('--max-price', type=float, default=2000)
        parser.add_argument('--apply', action='store_true', help='Delete the previewed products.')

    def handle(self, *args, **options):
        try:
            after = datetime.fromisoformat(options['after'])
            before = datetime.fromisoformat(options['before'])
        except ValueError as exc:
            raise CommandError('Use ISO timestamps, including a timezone offset.') from exc

        if timezone.is_naive(after) or timezone.is_naive(before):
            raise CommandError('Both timestamps must include a timezone offset, such as +00:00.')
        if after >= before:
            raise CommandError('--after must be earlier than --before.')

        candidates = list(
            Product.objects.filter(
                created_at__gte=after,
                created_at__lt=before,
                price__gte=options['min_price'],
                price__lte=options['max_price'],
            ).filter(cover__isnull=True) | Product.objects.filter(
                created_at__gte=after,
                created_at__lt=before,
                price__gte=options['min_price'],
                price__lte=options['max_price'],
                cover='')
        )
        candidates = {product.id: product for product in candidates}.values()

        self.stdout.write(self.style.WARNING(f'Products without covers found: {len(candidates)}'))
        for product in candidates:
            self.stdout.write(f'  {product.product_id}: {product.name} (${product.price})')

        if not options['apply']:
            self.stdout.write('Preview only. Re-run the same command with --apply to delete these rows.')
            return

        backup_path = f'/tmp/products_without_covers_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(backup_path, 'w', encoding='utf-8') as backup:
            json.dump(
                [
                    {
                        'id': product.id,
                        'product_id': product.product_id,
                        'name': product.name,
                        'price': str(product.price),
                        'created_at': product.created_at.isoformat(),
                    }
                    for product in candidates
                ],
                backup,
                indent=2,
            )

        deleted, _ = Product.objects.filter(id__in=[product.id for product in candidates]).delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted} database row(s). Backup saved to {backup_path}.'))
