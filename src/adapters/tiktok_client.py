import asyncio
import threading
from typing import Optional
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, GiftEvent
from ..models import SpawnTask, ActionType
from ..config import ConfigLoader
from ..core.queue_worker import QueueWorker


class TikTokReceiver:
    def __init__(self, config: ConfigLoader, worker: QueueWorker, username: Optional[str] = None):
        self.config = config
        self.worker = worker
        self.username = username or config.usuario_tiktok
        self.client: Optional[TikTokLiveClient] = None
        self._thread: Optional[threading.Thread] = None
        self.is_connected = False

    def start(self):
        """
        Inicia el cliente de TikTokLive en un hilo separado.
        """
        self._thread = threading.Thread(target=self._run_client, daemon=True)
        self._thread.start()

    def _run_client(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        print(f"\n[TIKTOK] Conectando al LIVE de @{self.username}...")
        self.client = TikTokLiveClient(unique_id=f"@{self.username}")

        @self.client.on(ConnectEvent)
        async def on_connect(event: ConnectEvent):
            self.is_connected = True
            print(f"[TIKTOK] ¡Conectado exitosamente al stream de @{self.username}!")
            print("[TIKTOK] Escuchando regalos en tiempo real...\n")

        @self.client.on(GiftEvent)
        async def on_gift(event: GiftEvent):
            try:
                # 1. Ignorar eventos intermedios mientras dure la racha (para no duplicar)
                if event.streaking:
                    return

                # 2. Extraer datos del regalo
                donor = event.user.unique_id if event.user else "Anonimo"
                donor_nick = event.user.nickname if event.user else donor
                gift_name = event.gift.name if event.gift else "Regalo"
                repeat_count = getattr(event, "repeat_count", 1) or 1
                diamond_unit = event.gift.diamond_count if event.gift else 1
                total_coins = repeat_count * diamond_unit

                print(f"[REGALO RECIBIDO] @{donor_nick} ({donor}) envió {gift_name} x{repeat_count} ({total_coins} monedas)")

                # 3. Verificar si corresponde a comandos especiales (ayuda / sabotaje)
                special_cmd = self._check_special_command(total_coins)
                if special_cmd:
                    task = SpawnTask(
                        action_type=ActionType.COMMAND,
                        command=special_cmd["comando"],
                        donor=donor_nick,
                        description=f"{special_cmd['descripcion']} ({gift_name} x{repeat_count})"
                    )
                    self.worker.enqueue(task)
                    return

                # 4. Si es una racha de regalos de bajo costo (ej. Rosas de 1 moneda x 5),
                # encolamos N spawns individuales de ese nivel
                if repeat_count > 1 and diamond_unit <= 5:
                    cmd, categoria = self.config.get_demon_for_coins(diamond_unit)
                    for i in range(repeat_count):
                        task = SpawnTask(
                            action_type=ActionType.SPAWN,
                            command=cmd,
                            donor=donor_nick,
                            description=f"{categoria} #{i+1}/{repeat_count} ({gift_name})"
                        )
                        self.worker.enqueue(task)
                else:
                    # Regalo único o de alto valor: demonio según el total de monedas
                    cmd, categoria = self.config.get_demon_for_coins(total_coins)
                    task = SpawnTask(
                        action_type=ActionType.SPAWN,
                        command=cmd,
                        donor=donor_nick,
                        description=f"{categoria} ({gift_name} x{repeat_count})"
                    )
                    self.worker.enqueue(task)

            except Exception as e:
                print(f"[ERROR TIKTOK] Error al procesar regalo: {e}")

        try:
            loop.run_until_complete(self.client.start())
        except Exception as e:
            print(f"[ERROR TIKTOK] Desconexion o fallo de cliente: {e}")
        finally:
            self.is_connected = False

    def _check_special_command(self, coins: int) -> Optional[dict]:
        especiales = self.config.comandos_especiales
        for ayuda in especiales.get("ayudas", []):
            if ayuda.get("monedas") == coins:
                return ayuda
        for sabotaje in especiales.get("sabotajes", []):
            if sabotaje.get("monedas") == coins:
                return sabotaje
        return None
