import ctypes
import threading
import time
from typing import Callable
import serial
import serial.tools.list_ports
from core.config import get_buttons_config

user32 = ctypes.windll.user32

# Mouse flags
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040

KEYEVENTF_KEYUP = 0x0002

# Windows virtual key codes
VK_CODES: dict[str, int] = {
    # Common keys
    "Space": 0x20,
    "Enter": 0x0D,
    "Escape": 0x1B,
    "Shift": 0x10,
    "Ctrl": 0x11,
    "Alt": 0x12,
    "Tab": 0x09,
    "Backspace": 0x08,
    "Caps Lock": 0x14,
    
    # Navigation
    "Up Arrow": 0x26,
    "Down Arrow": 0x28,
    "Left Arrow": 0x25,
    "Right Arrow": 0x27,
    "Insert": 0x2D,
    "Delete": 0x2E,
    "Home": 0x24,
    "End": 0x23,
    "Page Up": 0x21,
    "Page Down": 0x22,
    
    # Letters A-Z
    **{chr(c): c for c in range(0x41, 0x5B)},
    
    # Numbers 0-9
    **{chr(c): c for c in range(0x30, 0x3A)},
    
    # Function keys F1-F12
    **{f"F{i}": 0x70 + (i - 1) for i in range(1, 13)},
}

# Backward compatibility constants
VK_RETURN = 0x0D
VK_SHIFT = 0x10
VK_ESCAPE = 0x1B
VK_R = 0x52
BTNEXA_KEY = VK_R
BTNEXB_KEY = VK_SHIFT
BTNEXC_KEY = VK_ESCAPE

# Available actions for UI dropdowns and configurations
AVAILABLE_ACTIONS: list[str] = [
    "Left Click",
    "Right Click",
    "Middle Click",
    "Space",
    "Enter",
    "Escape",
    "Shift",
    "Ctrl",
    "Alt",
    "Tab",
    "Backspace",
    # Letters
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
    "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
    # Numbers
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    # Navigation
    "Up Arrow", "Down Arrow", "Left Arrow", "Right Arrow",
    # Function keys
    "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",
]

DEFAULT_BUTTON_MAPPINGS: dict[str, str] = {
    "trigger": "Left Click",
    "secondary": "Right Click",
    "btnexA": "R",
    "btnexB": "Shift",
    "btnexC": "Escape",
}

BUTTON_DEFINITIONS = [
    {
        "key": "trigger",
        "name": "Trigger (TRIGGER)",
        "desc": "Main gun trigger",
        "default": "Left Click",
    },
    {
        "key": "secondary",
        "name": "Secondary (SECONDARY)",
        "desc": "Secondary gun button",
        "default": "Right Click",
    },
    {
        "key": "btnexA",
        "name": "Custom Button A",
        "desc": "Configurable button",
        "default": "R",
    },
    {
        "key": "btnexB",
        "name": "Custom Button B",
        "desc": "Configurable button",
        "default": "Shift",
    },
    {
        "key": "btnexC",
        "name": "Custom Button C",
        "desc": "Configurable button",
        "default": "Escape",
    },
]

MOUSE_EVENT_MAP = {
    "left click": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP),
    "mouse_left": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP),
    "right click": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP),
    "mouse_right": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP),
    "middle click": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP),
    "mouse_middle": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP),
}

def send_mouse_event(flags: int) -> None:
    user32.mouse_event(flags, 0, 0, 0, 0)

def send_key_event(vk_code: int, key_up: bool = False) -> None:
    flags = KEYEVENTF_KEYUP if key_up else 0
    user32.keybd_event(vk_code, 0, flags, 0)

def get_virtual_key_code(key_name: str) -> int | None:
    norm = key_name.strip()
    if not norm:
        return None

    lookup = {k.lower(): v for k, v in VK_CODES.items()}
    aliases = {
        "esc": 0x1B,
        "escape": 0x1B,
        "return": 0x0D,
        "enter": 0x0D,
        "control": 0x11,
        "ctrl": 0x11,
        "shift": 0x10,
        "alt": 0x12,
        "space": 0x20,
        "spacebar": 0x20,
        "tab": 0x09,
        "backspace": 0x08,
        "caps": 0x14,
        "capslock": 0x14,
        "caps lock": 0x14,
        "up": 0x26,
        "down": 0x28,
        "left": 0x25,
        "right": 0x27,
        "arrowup": 0x26,
        "arrowdown": 0x28,
        "arrowleft": 0x25,
        "arrowright": 0x27,
        "up arrow": 0x26,
        "down arrow": 0x28,
        "left arrow": 0x25,
        "right arrow": 0x27,
    }
    
    lookup.update(aliases)

    key_lower = norm.lower()
    if key_lower in lookup:
        return lookup[key_lower]

    if len(norm) == 1:
        try:
            res = user32.VkKeyScanW(ord(norm))
            vk = res & 0xFF
            if vk != 0xFF and vk != 0:
                return vk
        except Exception:
            pass

    return None

def trigger_action(action_name: str, is_down: bool) -> None:
    norm = action_name.strip().lower()
    if norm in MOUSE_EVENT_MAP:
        down_flag, up_flag = MOUSE_EVENT_MAP[norm]
        send_mouse_event(down_flag if is_down else up_flag)
        return

    vk = get_virtual_key_code(action_name)
    if vk is not None:
        send_key_event(vk, key_up=not is_down)

def list_serial_ports() -> list[tuple[str, str]]:
    ports = serial.tools.list_ports.comports()
    return [(p.device, p.description) for p in ports]

class GunController:
    def __init__(
        self,
        port: str = "AUTO",
        baudrate: int = 115200,
        is_screen_targeted: Callable[[], bool] | None = None,
        offscreen_reload: bool = False,
        button_mappings: dict[str, str] | None = None,
    ):
        self.port = port
        self.baudrate = baudrate
        self.is_screen_targeted = is_screen_targeted
        self.offscreen_reload = offscreen_reload

        if button_mappings is None:
            button_mappings = get_buttons_config()
        self.button_mappings: dict[str, str] = dict(button_mappings)

        self._serial: serial.Serial | None = None
        self._running = False
        self._thread: threading.Thread | None = None

        # Optional listener callback for UI status or debugging
        self.on_instruction_received: Callable[[str], None] | None = None

        self._trigger_offscreen_fired = False
        
        self.update_action_map(button_mappings)


    def _normalize_instruction(self, instruction: str) -> tuple[str, bool] | None:
        parts = instruction.split(":")
        if len(parts) != 2:
            return None

        button_name, state = parts[0].strip(), parts[1].strip()
        state_lower = state.lower()
        if state_lower in ("0", "down"):
            is_down = True
        elif state_lower in ("1", "up"):
            is_down = False
        else:
            return None

        if button_name.upper() == "TRIGGER":
            norm_name = "trigger"
        elif button_name.upper() == "SECONDARY":
            norm_name = "secondary"
        elif button_name in ("btnexA", "BTNEXTA"):
            norm_name = "btnexA"
        elif button_name in ("btnexB", "BTNEXTB"):
            norm_name = "btnexB"
        elif button_name in ("btnexC", "BTNEXTC"):
            norm_name = "btnexC"
        else:
            norm_name = button_name

        return norm_name, is_down

    def update_action_map(self, mappings: dict[str, str]) -> None:
        self.button_mappings = dict(mappings)

    def execute_button(self, button_name: str, is_down: bool) -> None:
        action = self.button_mappings.get(button_name)
        if action:
            trigger_action(action, is_down=is_down)

    def _handle_trigger_down(self) -> None:
        if self.offscreen_reload and self.is_screen_targeted is not None:
            if not self.is_screen_targeted():
                # Pointed off-screen -> trigger btnexA instead of shooting
                # Only fire once when going offscreen
                if not self._trigger_offscreen_fired:
                    self._trigger_btnexA_pulse()
                    self._trigger_offscreen_fired = True
                return

        self._trigger_offscreen_fired = False
        self.execute_button("trigger", is_down=True)

    def _handle_trigger_up(self) -> None:
        if self._trigger_offscreen_fired:
            self._trigger_offscreen_fired = False
            return
        if self._trigger_offscreen_fired:
            self._trigger_offscreen_fired = False
            return

        self.execute_button("trigger", is_down=False)

    def _trigger_btnexA_pulse(self) -> None:
        if not getattr(self, '_btnexA_firing', False):
            self._btnexA_firing = True
            self.execute_button("btnexA", is_down=True)
            time.sleep(0.04)
            self.execute_button("btnexA", is_down=False)
            self._btnexA_firing = False

    @staticmethod
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

                normalized = self._normalize_instruction(line)
                if not normalized:
                    continue

                button_name, is_down = normalized

                # Handle special cases
                if button_name == "trigger":
                    if is_down:
                        self._handle_trigger_down()
                    else:
                        self._handle_trigger_up()
                else:
                    # Generic button handling
                    self.execute_button(button_name, is_down)
            except Exception:
                break
        self._running = False
