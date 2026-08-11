from django.conf import settings

from .models import HomePageSettings


def site_settings(request):
    return {
        "home_settings": HomePageSettings.load(),
        "reown_project_id": settings.REOWN_PROJECT_ID,
    }
