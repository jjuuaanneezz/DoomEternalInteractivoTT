import ctypes
from ctypes import wintypes
import time
from typing import Optional

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
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

# Scancodes de hardware estándar (DirectX / idTech)
SCANCODE_TILDE = 0x29      # Tecla ` o ~ (debajo de Escape)
SCANCODE_RETURN = 0x1C     # Tecla Enter
SCANCODE_ESCAPE = 0x01     # Tecla Esc


class DoomInjector:
    def __init__(self, console_key_scancode: int = SCANCODE_TILDE):
        self.user32 = ctypes.windll.user32
        self.console_key = console_key_scancode
        self.last_found_hwnd: Optional[int] = None

    def find_doom_window(self) -> Optional[int]:
        """
        Busca la ventana de Doom Eternal por título o clase.
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

        # Intento de búsqueda directa
        direct_hwnd = self.user32.FindWindowW(None, "DOOMEternal")
        if direct_hwnd:
            self.last_found_hwnd = direct_hwnd
            return direct_hwnd

        return None

    def focus_window(self, hwnd: Optional[int] = None) -> bool:
        """
        Trae la ventana de Doom al frente.
        """
        target_hwnd = hwnd or self.last_found_hwnd or self.find_doom_window()
        if not target_hwnd:
            return False

        # Si está minimizada, restaurar
        if self.user32.IsIconic(target_hwnd):
            self.user32.ShowWindow(target_hwnd, 9)  # SW_RESTORE

        # Adjuntar hilo de entrada para garantizar el foco en Windows
        current_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        window_thread_id = self.user32.GetWindowThreadProcessId(target_hwnd, None)

        self.user32.AttachThreadInput(current_thread_id, window_thread_id, True)
        self.user32.SetForegroundWindow(target_hwnd)
        self.user32.SetFocus(target_hwnd)
        self.user32.AttachThreadInput(current_thread_id, window_thread_id, False)

        time.sleep(0.05)
        return True

    def _send_key(self, scancode: int, is_up: bool = False):
        flags = KEYEVENTF_SCANCODE
        if is_up:
            flags |= KEYEVENTF_KEYUP

        extra = ctypes.c_ulong(0)
        ii_ = InputI()
        ii_.ki = KeyBdInput(0, scancode, flags, 0, ctypes.pointer(extra))
        x = Input(ctypes.c_ulong(INPUT_KEYBOARD), ii_)
        self.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    def press_and_release(self, scancode: int, hold_seconds: float = 0.02):
        self._send_key(scancode, is_up=False)
        time.sleep(hold_seconds)
        self._send_key(scancode, is_up=True)
        time.sleep(hold_seconds)

    def type_char_unicode(self, ch: str, hold_seconds: float = 0.01):
        extra = ctypes.c_ulong(0)
        code = ord(ch)

        # Key down
        ii_down = InputI()
        ii_down.ki = KeyBdInput(0, code, KEYEVENTF_UNICODE, 0, ctypes.pointer(extra))
        x_down = Input(ctypes.c_ulong(INPUT_KEYBOARD), ii_down)
        self.user32.SendInput(1, ctypes.pointer(x_down), ctypes.sizeof(x_down))

        time.sleep(hold_seconds)

        # Key up
        ii_up = InputI()
        ii_up.ki = KeyBdInput(0, code, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
        x_up = Input(ctypes.c_ulong(INPUT_KEYBOARD), ii_up)
        self.user32.SendInput(1, ctypes.pointer(x_up), ctypes.sizeof(x_up))

        time.sleep(hold_seconds)

    def type_string(self, text: str):
        for ch in text:
            self.type_char_unicode(ch)

    def execute_command(self, command: str, focus_first: bool = True) -> bool:
        """
        Abre la consola de Doom, escribe el comando, pulsa Enter y cierra la consola.
        """
        if focus_first:
            self.focus_window()

        # 1. Abrir consola
        self.press_and_release(self.console_key, hold_seconds=0.03)
        time.sleep(0.04)

        # 2. Escribir comando
        self.type_string(command)
        time.sleep(0.03)

        # 3. Presionar Enter
        self.press_and_release(SCANCODE_RETURN, hold_seconds=0.03)
        time.sleep(0.04)

        # 4. Cerrar consola
        self.press_and_release(self.console_key, hold_seconds=0.03)
        time.sleep(0.02)
        return True

    def panic_kill_all(self, focus_first: bool = True) -> bool:
        """
        Ejecuta el botón de pánico en Doom para eliminar a todos los demonios vivos.
        """
        return self.execute_command("mh_killAi", focus_first=focus_first)
