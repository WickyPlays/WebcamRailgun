import ctypes
import threading
import time
from typing import Callable
import serial
import serial.tools.list_ports

user32 = ctypes.windll.user32

# Mouse flags
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010

# Windows virtual key codes
VK_RETURN = 0x0D
VK_SHIFT = 0x10
VK_ESCAPE = 0x1B
VK_R = 0x52
KEYEVENTF_KEYUP = 0x0002

# Button name mappings
# TODO: Able to be changed later
BTNEX1_KEY = VK_R
BTNEX2_KEY = VK_SHIFT
BTNEX3_KEY = VK_ESCAPE

def send_mouse_event(flags: int) -> None:
    user32.mouse_event(flags, 0, 0, 0, 0)

def send_key_event(vk_code: int, key_up: bool = False) -> None:
    flags = KEYEVENTF_KEYUP if key_up else 0
    user32.keybd_event(vk_code, 0, flags, 0)


def list_serial_ports() -> list[tuple[str, str]]:
    ports = serial.tools.list_ports.comports()
    return [(p.device, p.description) for p in ports]

class GunController:
    def __init__(
        self,
        port: str = "AUTO",
        baudrate: int = 115200,
        is_screen_targeted: Callable[[], bool] | None = None,
        offscreen_reload: bool = True,
    ):
        self.port = port
        self.baudrate = baudrate
        self.is_screen_targeted = is_screen_targeted
        self.offscreen_reload = offscreen_reload

        self._serial: serial.Serial | None = None
        self._running = False
        self._thread: threading.Thread | None = None

        # Optional listener callback for UI status or debugging
        self.on_instruction_received: Callable[[str], None] | None = None

        # Instruction to action mapping
        self.action_map: dict[str, Callable[[], None]] = {
            "TRIGGER:DOWN": self._handle_trigger_down,
            "TRIGGER:UP": self._handle_trigger_up,
            "SECONDARY:DOWN": lambda: send_mouse_event(MOUSEEVENTF_RIGHTDOWN),
            "SECONDARY:UP": lambda: send_mouse_event(MOUSEEVENTF_RIGHTUP),
            "btnex1:DOWN": self._handle_btnex1_down,
            "btnex1:UP": self._handle_btnex1_up,
            "btnex2:DOWN": lambda: send_key_event(BTNEX2_KEY, key_up=False),
            "btnex2:UP": lambda: send_key_event(BTNEX2_KEY, key_up=True),
            "btnex3:DOWN": lambda: send_key_event(BTNEX3_KEY, key_up=False),
            "btnex3:UP": lambda: send_key_event(BTNEX3_KEY, key_up=True),
        }

    def _handle_trigger_down(self) -> None:
        if self.offscreen_reload and self.is_screen_targeted is not None:
            if not self.is_screen_targeted():
                # Pointed off-screen -> trigger btnex1 instead of shooting
                self._trigger_btnex1_pulse()
                return

        # Pointed at screen -> primary fire (left click)
        send_mouse_event(MOUSEEVENTF_LEFTDOWN)

    def _handle_trigger_up(self) -> None:
        send_mouse_event(MOUSEEVENTF_LEFTUP)

    def _handle_btnex1_down(self) -> None:
        send_key_event(BTNEX1_KEY, key_up=False)

    def _handle_btnex1_up(self) -> None:
        send_key_event(BTNEX1_KEY, key_up=True)

    def _trigger_btnex1_pulse(self) -> None:
        send_key_event(BTNEX1_KEY, key_up=False)
        time.sleep(0.04)
        send_key_event(BTNEX1_KEY, key_up=True)

    @staticmethod
    # TODO: Do we even need this?
    def auto_detect_port() -> str | None:
        ports = serial.tools.list_ports.comports()
        for p in ports:
            desc = p.description.lower()
            if any(k in desc for k in ("cp210", "ch340", "ch910", "uart", "usb serial", "esp32")):
                return p.device
        return ports[0].device if ports else None

    @property
    def is_connected(self) -> bool:
        return self._running and self._serial is not None and self._serial.is_open

    def start(self) -> bool:
        if self._running:
            return True

        target_port = self.port
        if not target_port or target_port.upper() == "AUTO":
            detected = self.auto_detect_port()
            if not detected:
                return False
            target_port = detected

        try:
            self._serial = serial.Serial(target_port, self.baudrate, timeout=0.5)
            self._running = True
            self._thread = threading.Thread(target=self.start_event_listener, daemon=True)
            self._thread.start()
            return True
        except Exception:
            self._serial = None
            self._running = False
            return False

    def stop(self) -> None:
        self._running = False
        if self._serial:
            try:
                self._serial.close()
            except Exception:
                pass
            self._serial = None

    def start_event_listener(self) -> None:
        while self._running and self._serial and self._serial.is_open:
            try:
                line = self._serial.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                if self.on_instruction_received:
                    self.on_instruction_received(line)

                action = self.action_map.get(line)
                if action:
                    action()
            except Exception:
                break
        self._running = False
