import json
import os
import random
from typing import List, Optional, Tuple
from .models import DemonTier, SpawnTask, ActionType


class ConfigLoader:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.usuario_tiktok: str = ""
        self.max_spawns_por_minuto: int = 20
        self.delay_entre_spawns_segundos: float = 2.0
        self.tecla_consola: str = "`"
        self.comando_panico: str = "mh_killAi"
        self.rangos: List[DemonTier] = []
        self.comandos_especiales: dict = {}
        self.load()

    def load(self) -> None:
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Archivo de configuración no encontrado: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.usuario_tiktok = data.get("usuario_tiktok", "streamer")
        self.max_spawns_por_minuto = int(data.get("max_spawns_por_minuto", 20))
        self.delay_entre_spawns_segundos = float(data.get("delay_entre_spawns_segundos", 2.0))
        self.tecla_consola = data.get("tecla_consola", "`")
        self.comando_panico = data.get("comando_panico", "mh_killAi")
        self.comandos_especiales = data.get("comandos_especiales", {})

        self.rangos = []
        for r in data.get("rangos_donaciones", []):
            self.rangos.append(
                DemonTier(
                    min_coins=r.get("min_monedas", 1),
                    max_coins=r.get("max_monedas", 999999),
                    category=r.get("categoria", "Desconocido"),
                    demons=r.get("demonios", ["ai/fodder/imp"])
                )
            )

    def get_demon_for_coins(self, coins: int) -> Tuple[str, str]:
        """
        Retorna (comando_chrispy, categoria) según las monedas.
        """
        for tier in self.rangos:
            if tier.min_coins <= coins <= tier.max_coins:
                chosen_demon = random.choice(tier.demons)
                return f"chrispy {chosen_demon}", tier.category

        # Si supera o no coincide, buscar el rango más alto
        if self.rangos:
            tier = self.rangos[-1]
            chosen_demon = random.choice(tier.demons)
            return f"chrispy {chosen_demon}", tier.category

        return "chrispy ai/fodder/imp", "Fodder por defecto"
