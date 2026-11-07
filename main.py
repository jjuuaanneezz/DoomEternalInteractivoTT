import argparse
import ctypes
import os
import sys
import time
import threading
from src.config import ConfigLoader
from src.adapters.doom_injector import DoomInjector
from src.core.rate_limiter import RateLimiter
from src.core.queue_worker import QueueWorker
from src.adapters.tiktok_client import TikTokReceiver
from src.models import SpawnTask, ActionType

# Virtual Key de Windows para F12 (Pánico)
VK_F12 = 0x7B


def print_bind_reminder():
    print("\n" + "-"*65)
    print(" [SISTEMA SILENCIOSO ACTIVO]: No abre la consola ni interrumpe WASD.")
    print(" Usa la tecla [F5] vinculada a 'exec live_cmd.cfg'.")
    print(" (Si ya tenias el juego abierto, escribe 1 sola vez en consola:")
    print('  bind F5 "exec live_cmd.cfg"')
    print(" En proximas partidas se cargara automaticamente via autoexec.cfg)")
    print("-"*65)


def listen_global_panic_hotkey(worker: QueueWorker, stop_event: threading.Event):
    """
    Hilo en segundo plano que escucha la tecla F12 globalmente
    para activar el botón de pánico en cualquier momento durante la partida.
    """
    user32 = ctypes.windll.user32
    while not stop_event.is_set():
        if user32.GetAsyncKeyState(VK_F12) & 0x8000:
            print("\n[HOTKEY F12 DETECTADA] ¡Activando Boton de Panico!")
            worker.enqueue(
                SpawnTask(
                    action_type=ActionType.PANIC,
                    command="mh_killAi",
                    donor="Streamer (Hotkey F12)",
                    description="Limpieza de emergencia"
                )
            )
            time.sleep(1.0)
        time.sleep(0.05)


def run_test_mode(coins: int, config: ConfigLoader, injector: DoomInjector):
    cmd, categoria = config.get_demon_for_coins(coins)
    print("\n" + "="*65)
    print(f" MODO DE PRUEBA: Donacion simulada de {coins} monedas")
    print(f" Categoria: {categoria}")
    print(f" Comando asignado: {cmd}")
    print("="*65)
    print_bind_reminder()

    print("\nPreparate... enviando a Doom Eternal en:")
    for i in range(3, 0, -1):
        print(f" {i}...")
        time.sleep(1.0)

    hwnd = injector.find_doom_window()
    if not hwnd:
        print("\n[AVISO] No se detecto la ventana de Doom Eternal abierta.")
        print("Asegurate de tener el juego abierto y en la arena.")
        print("Disparando comando de todos modos...\n")
    else:
        print(f"\n[OK] Ventana de Doom Eternal detectada (HWND: {hwnd}).")

    success = injector.execute_command(cmd)
    if success:
        print(f"[EXITO] Inyectado '{cmd}' mediante live_cmd.cfg + pulsacion F5 (sin consola).")
    else:
        print("[ERROR] No se pudo inyectar el comando.")


def run_panic_mode(injector: DoomInjector):
    print("\n[BOTON DE PANICO] Enviando mh_killAi a Doom Eternal mediante F5...")
    injector.panic_kill_all()
    print("[EXITO] Comando de pánico enviado.")


def run_live_mode(username: str, config: ConfigLoader, injector: DoomInjector, worker: QueueWorker):
    print("\n" + "="*65)
    print("       DOOM ETERNAL INTERACTIVO - TIKTOK LIVE")
    print("="*65)
    print(f" Streamer: @{username}")
    print(f" Limite de seguridad: {config.max_spawns_por_minuto} spawns/minuto")
    print(f" Delay minimo entre spawns: {config.delay_entre_spawns_segundos}s")
    print(" Inyeccion: Silenciosa en segundo plano (F5 -> live_cmd.cfg)")
    print(" Tecla de panico de emergencia en el teclado: [F12]")
    print("="*65)
    print_bind_reminder()

    # Iniciar worker
    worker.start()

    # Iniciar escucha de tecla de pánico global
    stop_event = threading.Event()
    panic_thread = threading.Thread(target=listen_global_panic_hotkey, args=(worker, stop_event), daemon=True)
    panic_thread.start()

    # Iniciar cliente de TikTok
    receiver = TikTokReceiver(config=config, worker=worker, username=username)
    receiver.start()

    print("\nBot interactivo funcionando. Presiona [Ctrl + C] para detener.\n")
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n[CERRANDO] Deteniendo bot y desconectando limpiamente...")
        stop_event.set()
        worker.stop()
        print("[OK] Bot interactivo apagado. ¡Buen stream!")


def main():
    parser = argparse.ArgumentParser(description="Doom Eternal Interactivo para TikTok LIVE")
    parser.add_argument("--test", type=int, help="Simula una donacion con el monto de monedas indicado (ej. --test 100)")
    parser.add_argument("--panic", action="store_true", help="Ejecuta de inmediato el comando de pánico (mh_killAi)")
    parser.add_argument("--streamer", type=str, help="Nombre de usuario de TikTok para conectar en vivo")
    args = parser.parse_args()

    try:
        config = ConfigLoader("config.json")
    except Exception as e:
        print(f"[ERROR] No se pudo cargar config.json: {e}")
        sys.exit(1)

    injector = DoomInjector()
    rate_limiter = RateLimiter(
        max_per_minute=config.max_spawns_por_minuto,
        min_delay_seconds=config.delay_entre_spawns_segundos
    )
    worker = QueueWorker(injector=injector, rate_limiter=rate_limiter)

    if args.panic:
        run_panic_mode(injector)
        return

    if args.test is not None:
        run_test_mode(args.test, config, injector)
        return

    streamer_user = args.streamer or config.usuario_tiktok
    if streamer_user and streamer_user != "nombre_de_usuario_tiktok":
        run_live_mode(streamer_user, config, injector, worker)
    else:
        print("\n[AVISO] No se proporciono un usuario de TikTok.")
        print("Uso:")
        print("  python main.py --test <monedas>       (Modo de prueba local)")
        print("  python main.py --streamer <usuario>   (Modo LIVE en tiempo real)")
        print("  python main.py --panic                (Boton de panico)")
        print("\nTambien puedes editar 'usuario_tiktok' dentro de config.json.\n")


if __name__ == "__main__":
    main()
