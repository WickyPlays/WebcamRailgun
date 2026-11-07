import asyncio
import sys
from pathlib import Path
from typing import Callable

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import flet as ft
from core.config import get_buttons_config, get_gun_config
from core.gun_input import GunController


def normalize_flet_key(key: str) -> str:
    k = (key or "").strip()
    if not k:
        return ""

    if len(k) == 1:
        return k.lower()

    lower = k.lower()
    if "shift" in lower:
        return "shift"
    if "control" in lower or "ctrl" in lower:
        return "ctrl"
    if "alt" in lower:
        return "alt"
    if lower in ("esc", "escape"):
        return "escape"
    if lower in ("enter", "return"):
        return "enter"
    if lower in ("space", "spacebar", " "):
        return "space"
    if lower == "tab":
        return "tab"
    if lower == "backspace":
        return "backspace"
    if "arrow" in lower or lower in ("up", "down", "left", "right"):
        if "up" in lower:
            return "up arrow"
        if "down" in lower:
            return "down arrow"
        if "left" in lower:
            return "left arrow"
        if "right" in lower:
            return "right arrow"
    if lower.startswith("f") and lower[1:].isdigit():
        return lower.lower()

    return lower


def gun_test_page(page: ft.Page, on_exit: Callable[[], None] | None = None):
    page.clean()
    page.title = "Webcam Railgun - Gun Test"
    page.window.full_screen = True
    page.bgcolor = ft.Colors.BLACK
    page.padding = 0
    page.spacing = 0

    loop = asyncio.get_event_loop()
    btn_cfg = get_buttons_config()
    gun_cfg = get_gun_config()

    # The 5 defined buttons on the hardware gun (strictly btnexA, btnexB, btnexC)
    GUN_DEFINED_MAP = {
        "trigger": ("Trigger", "TRIGGER"),
        "secondary": ("Secondary", "SECONDARY"),
        "btnexA": ("Custom Button A", "btnexA"),
        "btnexB": ("Custom Button B", "btnexB"),
        "btnexC": ("Custom Button C", "btnexC"),
    }

    # Map configured keys or default keys to the 5 defined buttons
    cfg_trigger = normalize_flet_key(btn_cfg.get("trigger", "Left Click"))
    cfg_secondary = normalize_flet_key(btn_cfg.get("secondary", "Right Click"))
    cfg_btnexA = normalize_flet_key(btn_cfg.get("btnexA", "R"))
    cfg_btnexB = normalize_flet_key(btn_cfg.get("btnexB", "Shift"))
    cfg_btnexC = normalize_flet_key(btn_cfg.get("btnexC", "Escape"))

    KEYBOARD_DEFINED_MAP = {
        cfg_btnexA: ("Custom Button A", "btnexA"),
        cfg_btnexB: ("Custom Button B", "btnexB"),
        cfg_btnexC: ("Custom Button C", "btnexC"),
        cfg_trigger: ("Trigger", "TRIGGER"),
        cfg_secondary: ("Secondary", "SECONDARY"),
        # Built-in defaults
        "r": ("Custom Button A", "btnexA"),
        "shift": ("Custom Button B", "btnexB"),
        "escape": ("Custom Button C", "btnexC"),
        "esc": ("Custom Button C", "btnexC"),
    }

    # UI controls
    button_title = ft.Text(
        value="",
        size=64,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
        text_align=ft.TextAlign.CENTER,
    )

    button_subtitle = ft.Text(
        value="",
        size=24,
        color=ft.Colors.GREY_400,
        text_align=ft.TextAlign.CENTER,
    )

    fade_container = ft.Container(
        content=ft.Column(
            [
                button_title,
                button_subtitle,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        ),
        opacity=0.0,
        animate_opacity=ft.Animation(800, ft.AnimationCurve.EASE_OUT),
        alignment=ft.Alignment.CENTER,
    )

    fade_seq = 0

    def show_button(title: str, sub: str):
        nonlocal fade_seq
        fade_seq += 1
        current_seq = fade_seq

        async def _animate():
            button_title.value = title
            button_subtitle.value = sub
            fade_container.opacity = 1.0
            page.update()

            await asyncio.sleep(0.4)
            if fade_seq == current_seq:
                fade_container.opacity = 0.0
                page.update()

        page.run_task(_animate)

    gun_controller: GunController | None = None
    is_closing = False

    def quit_app():
        nonlocal gun_controller, is_closing
        if is_closing:
            return
        is_closing = True

        if gun_controller:
            try:
                gun_controller.stop()
            except Exception:
                pass
            gun_controller = None

        page.on_keyboard_event = None

        if on_exit:
            on_exit()
        else:
            page.window.close()

    def handle_gun_instruction(line: str):
        cleaned = line.strip()
        if not cleaned or cleaned.startswith("STATUS:"):
            return

        if ":" in cleaned:
            btn_part, state = cleaned.split(":", 1)
            btn_key = btn_part.strip()
            state = state.strip().upper()

            if state in ("DOWN", "0"):
                if btn_key.upper() == "TRIGGER":
                    norm_key = "trigger"
                elif btn_key.upper() == "SECONDARY":
                    norm_key = "secondary"
                else:
                    norm_key = btn_key

                if norm_key in GUN_DEFINED_MAP:
                    title, sub = GUN_DEFINED_MAP[norm_key]
                    show_button(title, sub)
                else:
                    # User pressed a button other than the 5 defined -> quit
                    quit_app()

    # Start GunController if enabled
    if gun_cfg.get("enabled", True):
        gun_controller = GunController(
            port=gun_cfg.get("port", "AUTO"),
            baudrate=gun_cfg.get("baudrate", 115200),
            offscreen_reload=False,  # In test mode, detect raw button presses directly
        )
        # Intercept instructions safely onto main event loop
        gun_controller.on_instruction_received = lambda line: loop.call_soon_threadsafe(
            handle_gun_instruction, line
        )
        gun_controller.start()

    def on_keyboard_event(e: ft.KeyboardEvent):
        key_norm = normalize_flet_key(e.key)
        if not key_norm:
            return

        if key_norm in KEYBOARD_DEFINED_MAP:
            title, sub = KEYBOARD_DEFINED_MAP[key_norm]
            show_button(title, f"{sub} (Keyboard)")
        else:
            # Any key other than the 5 defined -> quit
            quit_app()

    page.on_keyboard_event = on_keyboard_event

    def on_mouse_left(e):
        show_button("Trigger", "TRIGGER (Left Click)")

    def on_mouse_right(e):
        show_button("Secondary", "SECONDARY (Right Click)")

    # Status footer indicator
    port_text = gun_controller.port if gun_controller else "Disabled"
    status_hint = ft.Text(
        value=f"Webcam Railgun Test Mode (Port: {port_text}) • Press gun button to test • Press any other button to quit",
        size=13,
        color=ft.Colors.GREY_600,
        text_align=ft.TextAlign.CENTER,
    )

    # 20px thick solid white border around full screen
    root_container = ft.Container(
        expand=True,
        bgcolor=ft.Colors.BLACK,
        border=ft.Border.all(20, ft.Colors.WHITE),
        content=ft.GestureDetector(
            expand=True,
            on_tap_down=on_mouse_left,
            on_secondary_tap_down=on_mouse_right,
            content=ft.Stack(
                [
                    fade_container,
                    ft.Container(
                        content=status_hint,
                        alignment=ft.Alignment.BOTTOM_CENTER,
                        padding=ft.Padding.only(bottom=15),
                    ),
                ],
                expand=True,
            ),
        ),
    )

    page.add(root_container)

    def on_window_event(e: ft.WindowEvent):
        if e.type == ft.WindowEventType.CLOSE:
            quit_app()

    page.window.on_event = on_window_event
    page.on_disconnect = lambda _: quit_app()

def main(page: ft.Page):
    gun_test_page(page)


if __name__ == "__main__":
    ft.run(main, assets_dir=str(PROJECT_ROOT / "flet_app" / "assets"))
