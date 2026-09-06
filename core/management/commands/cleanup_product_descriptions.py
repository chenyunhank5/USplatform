import html
import json
import re
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Product


FENCE_START_RE = re.compile(r'^\s*```(?:html)?\s*', re.IGNORECASE)
FENCE_END_RE = re.compile(r'\s*```\s*$', re.IGNORECASE)
HEADING_RE = re.compile(r'<h2\b[^>]*>(.*?)</h2>', re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r'<[^>]+>')


def _heading_text(value):
    return html.unescape(TAG_RE.sub('', value)).strip().casefold()


def clean_description(description, product_name):
    cleaned = description or ''
    cleaned = FENCE_START_RE.sub('', cleaned, count=1)
    cleaned = FENCE_END_RE.sub('', cleaned, count=1)

    heading = HEADING_RE.search(cleaned)
    heading_text = _heading_text(heading.group(1))
    product_text = product_name.strip().casefold()
    if heading and heading_text and (
        heading_text == product_text
        or product_text.startswith(heading_text)
    ):
        cleaned = cleaned[:heading.start()] + cleaned[heading.end():]

    return cleaned.strip()


class Command(BaseCommand):
    help = 'Find and optionally clean accidental Markdown fences and matching product-title headings.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Apply the cleanup. Without this flag, only a preview is shown.',
        )
        parser.add_argument(
            '--backup-path',
            help='Optional JSON backup path used when applying changes.',
        )

    def handle(self, *args, **options):
        candidates = []
        for product in Product.objects.only('id', 'product_id', 'name', 'description').iterator():
            cleaned = clean_description(product.description, product.name)
            if cleaned != (product.description or ''):
                candidates.append((product, cleaned))

        self.stdout.write(f'Products needing cleanup: {len(candidates)}')
        for product, cleaned in candidates[:20]:
            self.stdout.write(f'  {product.product_id}: {product.name}')
        if len(candidates) > 20:
            self.stdout.write(f'  ... and {len(candidates) - 20} more')

        if not options['apply']:
            self.stdout.write('Preview only. Re-run with --apply to make changes.')
            return

        backup_path = options.get('backup_path')
        if not backup_path:
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f'/tmp/product_descriptions_backup_{timestamp}.json'

        backup = [
            {
                'id': product.id,
                'product_id': product.product_id,
                'name': product.name,
                'description': product.description or '',
            }
            for product, _ in candidates
        ]
        Path(backup_path).write_text(
            json.dumps(backup, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )

        for product, cleaned in candidates:
            product.description = cleaned
        if candidates:
            Product.objects.bulk_update([product for product, _ in candidates], ['description'])

        self.stdout.write(self.style.SUCCESS(
            f'Cleaned {len(candidates)} products. Backup saved to {backup_path}'
        ))
