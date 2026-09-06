from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from core.models import UserProfile


class Command(BaseCommand):
    help = 'Hide inactive guest accounts and delete only safe, inactive guest accounts.'

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(hours=4)
        guests = UserProfile.objects.select_related('user').filter(
            user__username__startswith='guest-',
        ).filter(
            Q(last_activity_at__lte=cutoff)
            | Q(last_activity_at__isnull=True, registration_time__lte=cutoff)
        )

        hidden_count = guests.update(is_hidden_from_staff=True)
        deleted_count = 0

        for profile in guests.select_related('user'):
            user = profile.user
            has_related_data = any((
                profile.balance != 0,
                profile.frozen_amount != 0,
                user.user_orders.exists(),
                user.withdrawalrequest_set.exists(),
                user.deposit_records.exists(),
                profile.referral_commissions.exists(),
                profile.generated_referral_commissions.exists(),
                profile.lucky_rewards.exists(),
                profile.successive_order_plans.exists(),
                user.support_messages.exists(),
            ))

            if not has_related_data:
                user.delete()
                deleted_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Hidden {hidden_count} inactive guests; deleted {deleted_count} safe guests.'
            )
        )
