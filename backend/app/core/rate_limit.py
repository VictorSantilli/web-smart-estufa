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
    # Acima disso, chaves sem tentativas recentes são descartadas (limita o uso de memória).
    SWEEP_THRESHOLD = 10_000

    def __init__(self, max_hits: int, window_seconds: float) -> None:
        self.max_hits = max_hits
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _sweep(self, now: float) -> None:
        stale = [k for k, hits in self._hits.items() if not hits or now - hits[-1] > self.window]
        for key in stale:
            del self._hits[key]

    def hit(self, key: str) -> bool:
        """Registra uma tentativa. Retorna False se o limite foi excedido."""
        now = time.monotonic()
        with self._lock:
            if len(self._hits) >= self.SWEEP_THRESHOLD:
                self._sweep(now)
            hits = self._hits[key]
            while hits and now - hits[0] > self.window:
                hits.popleft()
            if len(hits) >= self.max_hits:
                return False
            hits.append(now)
            return True

    def __len__(self) -> int:
        return len(self._hits)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


login_ip_limiter = SlidingWindowLimiter(
    max_hits=get_settings().login_ip_max_per_minute, window_seconds=60
)
