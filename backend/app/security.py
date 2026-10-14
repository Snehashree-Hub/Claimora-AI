from collections import defaultdict, deque
from threading import Lock
from time import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class ClaimoraSecurityMiddleware(BaseHTTPMiddleware):
    """Baseline security headers, request-size checks and login rate limiting."""

    MAX_REQUEST_BYTES = 15 * 1024 * 1024
    LOGIN_WINDOW_SECONDS = 60
    LOGIN_MAX_ATTEMPTS = 10

    def __init__(self, app):
        super().__init__(app)
        self.attempts = defaultdict(deque)
        self.lock = Lock()

    async def dispatch(self, request, call_next):
        content_length = request.headers.get("content-length")

        if content_length:
            try:
                if int(content_length) > self.MAX_REQUEST_BYTES:
                    return JSONResponse(
                        {"detail": "Request too large."},
                        status_code=413,
                    )
            except ValueError:
                return JSONResponse(
                    {"detail": "Invalid Content-Length header."},
                    status_code=400,
                )

        path = request.url.path.lower()
        is_login_request = (
            request.method == "POST"
            and any(word in path for word in ("/login", "/token", "/signin"))
            and ("/auth" in path or path.endswith(("/login", "/token", "/signin")))
        )

        if is_login_request:
            client_ip = request.client.host if request.client else "unknown"
            key = (client_ip, path)
            now = time()

            with self.lock:
                queue = self.attempts[key]

                while queue and now - queue[0] > self.LOGIN_WINDOW_SECONDS:
                    queue.popleft()

                if len(queue) >= self.LOGIN_MAX_ATTEMPTS:
                    response = JSONResponse(
                        {"detail": "Too many login attempts. Please try again later."},
                        status_code=429,
                    )
                    response.headers["Retry-After"] = str(self.LOGIN_WINDOW_SECONDS)
                    return response

                queue.append(now)

        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store" if (
            "/claims" in path or "/documents" in path or "/auth" in path
        ) else response.headers.get("Cache-Control", "no-cache")

        return response
