def content_security_policy(get_response):
    def middleware(request):
        response = get_response(request)
        response["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; object-src 'none'; "
            "base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
        )
        return response

    return middleware
