from django.conf import settings

from .models import HomePageSettings


def site_settings(request):
    home_settings = getattr(request, "_home_page_settings", None)

    if home_settings is None:
        home_settings = HomePageSettings.load()
        request._home_page_settings = home_settings

    return {
        "home_settings": home_settings,
        "reown_project_id": settings.REOWN_PROJECT_ID,
    }
