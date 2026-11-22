from django.conf import settings
from django.middleware.locale import LocaleMiddleware
from django.utils import translation


class PreferredLanguageMiddleware(LocaleMiddleware):
    def process_request(self, request):
        preferred = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
        supported = dict(settings.LANGUAGES)
        language = preferred if preferred in supported else settings.LANGUAGE_CODE
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
