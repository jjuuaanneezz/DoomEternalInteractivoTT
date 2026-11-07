import queue
import threading
import time
from typing import Optional
from ..models import SpawnTask, ActionType
from ..adapters.doom_injector import DoomInjector
from .rate_limiter import RateLimiter


class QueueWorker:
    def __init__(self, injector: DoomInjector, rate_limiter: RateLimiter):
        self.injector = injector
        self.rate_limiter = rate_limiter
        self.task_queue: queue.Queue[SpawnTask] = queue.Queue()
        self.running = False
        self.worker_thread: Optional[threading.Thread] = None

    def start(self):
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def stop(self):
        self.running = False

    def enqueue(self, task: SpawnTask):
        # Si es botón de pánico, limpiar tareas pendientes y ejecutar prioritario
        if task.action_type == ActionType.PANIC:
            self.clear_queue()
            self.task_queue.put(task)
        else:
            self.task_queue.put(task)

    def clear_queue(self):
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
                self.task_queue.task_done()
            except queue.Empty:
                break

    def get_pending_count(self) -> int:
        return self.task_queue.qsize()

    def _worker_loop(self):
        while self.running:
            try:
                task = self.task_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                if task.action_type == ActionType.PANIC:
                    print(f"\n[PANICO] Ejecutando boton de panico solicitado por {task.donor}...")
                    self.injector.panic_kill_all()
                    print("[PANICO] Arena limpia exitosamente.")
                else:
                    # Esperar según el rate limiter
                    self.rate_limiter.wait_if_needed()
                    print(f"\n[EJECUTANDO] Donador: {task.donor} | Accion: {task.description}")
                    self.injector.execute_command(task.command)
            except Exception as e:
                print(f"[ERROR] Error al inyectar comando '{task.command}': {e}")
            finally:
                self.task_queue.task_done()

