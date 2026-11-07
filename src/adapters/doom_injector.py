import ctypes
from ctypes import wintypes
import os
import time
from typing import List, Optional

# Definición de estructuras de Windows API para SendInput
PUL = ctypes.POINTER(ctypes.c_ulong)


class KeyBdInput(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", PUL)
    ]


class HardwareInput(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD)
    ]


class MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", PUL)
    ]


class InputI(ctypes.Union):
    _fields_ = [
        ("ki", KeyBdInput),
        ("mi", MouseInput),
        ("hi", HardwareInput)
    ]


class Input(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("ii", InputI)
    ]


INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

# Tecla F5
VK_F5 = 0x74
SCANCODE_F5 = 0x3F


class DoomInjector:
    def __init__(self, trigger_key_vk: int = VK_F5, trigger_key_scancode: int = SCANCODE_F5):
        self.user32 = ctypes.windll.user32
        self.trigger_vk = trigger_key_vk
        self.trigger_scancode = trigger_key_scancode
        self.last_found_hwnd: Optional[int] = None

        # Rutas hacia el archivo live_cmd.cfg donde Doom ejecuta los comandos
        user_saved_games = os.path.expanduser("~\\Saved Games\\id Software\\DOOMEternal\\base")
        game_base = r"D:\SteamLibrary\steamapps\common\DOOMEternal\base"

        self.cfg_destinations: List[str] = [
            os.path.join(game_base, "live_cmd.cfg")
        ]
        if os.path.exists(user_saved_games):
            self.cfg_destinations.append(os.path.join(user_saved_games, "live_cmd.cfg"))

    def find_doom_window(self) -> Optional[int]:
        """
        Busca la ventana de Doom Eternal por título.
        """
        doom_hwnds = []

        def enum_windows_callback(hwnd, extra):
            if self.user32.IsWindowVisible(hwnd):
                length = self.user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    self.user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value
                    if "DOOMEternal" in title or "DOOM Eternal" in title:
                        doom_hwnds.append(hwnd)
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        self.user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)

        if doom_hwnds:
            self.last_found_hwnd = doom_hwnds[0]
            return doom_hwnds[0]

        direct_hwnd = self.user32.FindWindowW(None, "DOOMEternal")
        if direct_hwnd:
            self.last_found_hwnd = direct_hwnd
            return direct_hwnd

        return None

    def focus_window(self, hwnd: Optional[int] = None) -> bool:
        """
        Garantiza que Doom Eternal tenga el foco de entrada sin interrumpir el juego.
        """
        target_hwnd = hwnd or self.last_found_hwnd or self.find_doom_window()
        if not target_hwnd:
            return False

        if self.user32.IsIconic(target_hwnd):
            self.user32.ShowWindow(target_hwnd, 9)  # SW_RESTORE

        current_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        window_thread_id = self.user32.GetWindowThreadProcessId(target_hwnd, None)

        self.user32.AttachThreadInput(current_thread_id, window_thread_id, True)
        self.user32.SetForegroundWindow(target_hwnd)
        self.user32.SetFocus(target_hwnd)
        self.user32.AttachThreadInput(current_thread_id, window_thread_id, False)

        return True

    def _write_cmd_file(self, command: str) -> None:
        """
        Escribe el comando en live_cmd.cfg para que Doom lo ejecute con 'exec'.
        """
        for path in self.cfg_destinations:
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(f"{command}\n")
            except Exception as e:
                print(f"[AVISO] No se pudo escribir en {path}: {e}")

    def _press_trigger_key(self, hold_seconds: float = 0.02):
        """
        Envía una pulsación instantánea de F5 con scancode de hardware + VK.
        """
        extra = ctypes.c_ulong(0)

        # 1. Key Down (F5)
        ii_down = InputI()
        ii_down.ki = KeyBdInput(
            self.trigger_vk,
            self.trigger_scancode,
            KEYEVENTF_SCANCODE,
            0,
            ctypes.pointer(extra)
        )
        x_down = Input(ctypes.c_ulong(INPUT_KEYBOARD), ii_down)
        self.user32.SendInput(1, ctypes.pointer(x_down), ctypes.sizeof(x_down))

        time.sleep(hold_seconds)

        # 2. Key Up (F5)
        ii_up = InputI()
        ii_up.ki = KeyBdInput(
            self.trigger_vk,
            self.trigger_scancode,
            KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP,
            0,
            ctypes.pointer(extra)
        )
        x_up = Input(ctypes.c_ulong(INPUT_KEYBOARD), ii_up)
        self.user32.SendInput(1, ctypes.pointer(x_up), ctypes.sizeof(x_up))

    def execute_command(self, command: str, focus_first: bool = True) -> bool:
        """
        Escribe el comando en live_cmd.cfg y pulsa F5.
        La consola NUNCA se abre y no interfiere con WASD ni con el movimiento.
        """
        if focus_first:
            self.focus_window()

        # Escribir el comando dinámicamente
        self._write_cmd_file(command)

        # Disparar la tecla vinculada en Doom (F5)
        self._press_trigger_key(hold_seconds=0.02)
        return True

    def panic_kill_all(self, focus_first: bool = True) -> bool:
        """
        Ejecuta de inmediato mh_killAi mediante live_cmd.cfg + F5.
        """
        return self.execute_command("mh_killAi", focus_first=focus_first)
