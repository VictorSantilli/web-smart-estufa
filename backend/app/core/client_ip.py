"""IP do cliente para o limite de login.

O X-Forwarded-For é uma lista em que cada proxy ACRESCENTA no fim o endereço de quem o
chamou. As primeiras entradas vêm do próprio cliente e podem ser forjadas, então só é
confiável a entrada acrescentada pelo último proxy nosso: com N proxies confiáveis
(TRUSTED_PROXY_HOPS), o IP real é a N-ésima entrada contando do fim.
"""

from starlette.requests import Request

from app.core.config import get_settings


def client_ip(request: Request) -> str:
    hops = get_settings().trusted_proxy_hops
    peer = request.client.host if request.client else "unknown"
    if hops == 0:
        return peer
    forwarded = request.headers.get("x-forwarded-for", "")
    hosts = [h.strip() for h in forwarded.split(",") if h.strip()]
    if len(hosts) < hops:
        # Cabeçalho ausente ou mais curto que o esperado: a requisição não passou pelo
        # proxy configurado; o endereço da conexão é o único dado confiável.
        return peer
    return hosts[-hops]
