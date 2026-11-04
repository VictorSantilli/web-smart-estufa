"""Cabeçalhos de segurança em todas as respostas.

- CSP restritiva para o SPA: só scripts, estilos e chamadas da própria origem.
  `style-src 'unsafe-inline'` é necessário porque o Recharts e o React aplicam estilos
  em atributos `style`; scripts inline continuam bloqueados.
- A documentação (Swagger/ReDoc) carrega JS e CSS de CDN, então recebe uma CSP própria,
  liberando somente o CDN usado pelo FastAPI.
- Respostas da API não ficam em cache (contêm dados do usuário e tokens).
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

APP_CSP = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline'",
        # blob: = imagens das detecções, baixadas com o token e exibidas por URL local.
        "img-src 'self' data: blob:",
        "font-src 'self'",
        "connect-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]
)

DOCS_CDN = "https://cdn.jsdelivr.net"
DOCS_CSP = "; ".join(
    [
        "default-src 'self'",
        f"script-src 'self' 'unsafe-inline' {DOCS_CDN}",
        f"style-src 'self' 'unsafe-inline' {DOCS_CDN} https://fonts.googleapis.com",
        f"img-src 'self' data: https://fastapi.tiangolo.com {DOCS_CDN}",
        "font-src 'self' https://fonts.gstatic.com",
        f"connect-src 'self' {DOCS_CDN}",
        "worker-src 'self' blob:",
        "object-src 'none'",
        "frame-ancestors 'none'",
    ]
)

PERMISSIONS_POLICY = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, hsts: bool, api_prefix: str = "/api") -> None:
        super().__init__(app)
        self.hsts = hsts
        self.api_prefix = api_prefix.rstrip("/")
        self.docs_paths = tuple(f"{self.api_prefix}/{p}" for p in ("docs", "redoc", "openapi.json"))

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        path = request.url.path
        headers = response.headers
        headers.setdefault("X-Content-Type-Options", "nosniff")
        headers.setdefault("X-Frame-Options", "DENY")
        headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        headers.setdefault("Permissions-Policy", PERMISSIONS_POLICY)
        headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        headers.setdefault(
            "Content-Security-Policy", DOCS_CSP if path.startswith(self.docs_paths) else APP_CSP
        )
        if path == self.api_prefix or path.startswith(f"{self.api_prefix}/"):
            headers.setdefault("Cache-Control", "no-store")
        if self.hsts:
            headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response
