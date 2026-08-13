from django.conf import settings

from .models import DepositRecord, HomePageSettings, SupportMessage, WithdrawalRequest


def site_settings(request):
    home_settings = getattr(request, "_home_page_settings", None)

    if home_settings is None:
        home_settings = HomePageSettings.load()
        request._home_page_settings = home_settings

    unread_support_count = 0
    unread_system_count = 0

    if (
        request.user.is_authenticated
        and not request.user.is_staff
        and request.path.startswith("/user/")
    ):
        unread_support_count = SupportMessage.objects.filter(
            user=request.user,
            is_read_by_user=False,
        ).count()
        unread_system_count = (
            DepositRecord.objects.filter(
                user=request.user,
                is_read_by_user=False,
            ).count()
            + WithdrawalRequest.objects.filter(
                user=request.user,
                is_read_by_user=False,
            ).count()
        )

    unread_message_count = unread_support_count + unread_system_count

    return {
        "home_settings": home_settings,
        "reown_project_id": settings.REOWN_PROJECT_ID,
        "unread_message_count": unread_message_count,
        "unread_support_count": unread_support_count,
        "unread_system_count": unread_system_count,
    }
