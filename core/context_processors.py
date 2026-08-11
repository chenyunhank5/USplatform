from .models import HomePageSettings


def site_settings(request):
    return {
        "home_settings": HomePageSettings.load(),
    }
