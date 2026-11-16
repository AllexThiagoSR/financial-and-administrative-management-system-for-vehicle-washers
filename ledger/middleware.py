from django.utils.cache import patch_cache_control

def content_security_policy(get_response):
    def middleware(request):
        response = get_response(request)
        response["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; object-src 'none'; "
            "base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
        )
        if getattr(request, "user", None) and request.user.is_authenticated:
            patch_cache_control(response, private=True, no_store=True)
        return response

    return middleware
