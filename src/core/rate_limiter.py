import time
from collections import deque


class RateLimiter:
    def __init__(self, max_per_minute: int = 20, min_delay_seconds: float = 2.0):
        self.max_per_minute = max_per_minute
        self.min_delay_seconds = min_delay_seconds
        self.history = deque()
        self.last_action_time: float = 0.0

    def wait_if_needed(self) -> None:
        """
        Espera activamente hasta que haya un espacio disponible según
        el límite por minuto y el delay mínimo entre spawns.
        """
        now = time.time()

        # 1. Respetar el delay mínimo entre spawns consecutivos
        elapsed_since_last = now - self.last_action_time
        if elapsed_since_last < self.min_delay_seconds:
            time.sleep(self.min_delay_seconds - elapsed_since_last)

        # 2. Respetar la ventana deslizante de 60 segundos
        while True:
            now = time.time()
            # Limpiar eventos con más de 60 segundos
            while self.history and (now - self.history[0]) > 60.0:
                self.history.popleft()

            if len(self.history) < self.max_per_minute:
                # Hay cupo
                break

            # Si la ventana de 60s está llena, esperar hasta que expire el más viejo
            oldest = self.history[0]
            sleep_needed = 60.0 - (now - oldest) + 0.1
            if sleep_needed > 0:
                time.sleep(sleep_needed)

        # Registrar el evento actual
        now = time.time()
        self.history.append(now)
        self.last_action_time = now

    def get_queue_stats(self) -> dict:
        now = time.time()
        # Limpiar
        while self.history and (now - self.history[0]) > 60.0:
            self.history.popleft()

        return {
            "spawns_en_ultimo_minuto": len(self.history),
            "max_por_minuto": self.max_per_minute,
            "cupos_disponibles": max(0, self.max_per_minute - len(self.history))
        }
