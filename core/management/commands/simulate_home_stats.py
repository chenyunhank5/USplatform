import random
import re

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.management.base import BaseCommand

from core.models import HomePageSettings


class Command(BaseCommand):
    help = 'Update simulated homepage metrics without resetting them on refresh.'

    fields = (
        'online_users_value',
        'order_completion_value',
        'optimize_demand_value',
        'order_quantity_value',
    )

    def handle(self, *args, **options):
        settings, _ = HomePageSettings.objects.get_or_create(pk=1)
        changed = []

        for field in self.fields:
            current = self.parse_value(getattr(settings, field))
            if current is None:
                current = random.randint(500, 1000)
            elif field == 'order_completion_value':
                current += random.randint(1, 8)
            else:
                current += random.randint(-8, 8)

            setattr(settings, field, str(current))
            changed.append(field)

        settings.save(update_fields=[*changed, 'updated_at'])
        async_to_sync(get_channel_layer().group_send)(
            'homepage_stats',
            {
                'type': 'homepage_stats',
                'stats': {field: getattr(settings, field) for field in self.fields},
            },
        )
        self.stdout.write(self.style.SUCCESS('Homepage simulated metrics updated.'))

    @staticmethod
    def parse_value(value):
        match = re.search(r'\d+(?:\.\d+)?', str(value or ''))
        if not match:
            return None
        number = float(match.group())
        if str(value).lower().find('k') >= 0:
            number *= 1000
        return round(number)
