"""Limite simples de requisições por chave (ex.: IP no login), em memória.

Complementa o bloqueio por conta (Usuarios.TentativasFalhas/BloqueadoAte), que fica no
banco e vale para todas as réplicas. Este limite é por processo: com várias réplicas no
Container Apps ele vale por réplica, o que é aceitável como proteção extra.
"""

import threading
import time
from collections import defaultdict, deque

from app.core.config import get_settings


class SlidingWindowLimiter:
    def __init__(self, max_hits: int, window_seconds: float) -> None:
        self.max_hits = max_hits
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str) -> bool:
        """Registra uma tentativa. Retorna False se o limite foi excedido."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self.window:
                hits.popleft()
            if len(hits) >= self.max_hits:
                return False
            hits.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


login_ip_limiter = SlidingWindowLimiter(
    max_hits=get_settings().login_ip_max_per_minute, window_seconds=60
)
