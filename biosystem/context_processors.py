from django.conf import settings


def app_metadata(request):
    return {
        'app_version': settings.APP_VERSION,
        'support_contact': settings.SUPPORT_CONTACT,
    }
