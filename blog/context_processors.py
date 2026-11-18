from django.conf import settings

from blog.models import PersonalInfo


def site(request):
    """Expose the profile and canonical base URL to every template."""
    base = settings.SITE_URL or f"{request.scheme}://{request.get_host()}"
    return {
        "profile": PersonalInfo.get_solo(),
        "site_url": base,
        "canonical_url": base + request.path,
    }
