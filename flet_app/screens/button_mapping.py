import flet as ft
from core.config import get_buttons_config, save_setting
from core.gun_input import AVAILABLE_ACTIONS, BUTTON_DEFINITIONS, DEFAULT_BUTTON_MAPPINGS

def normalize_flet_key(key: str) -> str:
    k = (key or "").strip()
    if not k:
        return ""

    if len(k) == 1:
        return k.upper()

    lower = k.lower()
    if "shift" in lower:
        return "Shift"
    if "control" in lower or "ctrl" in lower:
        return "Ctrl"
    if "alt" in lower:
        return "Alt"
    if lower in ("esc", "escape"):
        return "Escape"
    if lower in ("enter", "return"):
        return "Enter"
    if lower in ("space", "spacebar", " "):
        return "Space"
    if lower == "tab":
        return "Tab"
    if lower == "backspace":
        return "Backspace"
    if "arrow" in lower or lower in ("up", "down", "left", "right"):
        if "up" in lower:
            return "Up Arrow"
        if "down" in lower:
            return "Down Arrow"
        if "left" in lower:
            return "Left Arrow"
        if "right" in lower:
            return "Right Arrow"
    if lower.startswith("f") and lower[1:].isdigit():
        return lower.upper()

    return k.title()

def button_mapping_page(page: ft.Page):
    page.clean()
    page.title = "Webcam Railgun - Button Mapping"
    page.window.width = 850
    page.window.height = 700

    saved_config = get_buttons_config()
    listening_target: str | None = None

    status_text = ft.Text(
        "Configure gun button mappings to mouse or keyboard controls.",
        size=14,
        color=ft.Colors.GREY_400,
    )

    dropdowns: dict[str, ft.Dropdown] = {}
    record_buttons: dict[str, ft.IconButton] = {}

    def start_listening(btn_key: str):
        nonlocal listening_target
        listening_target = btn_key

        target_def = next((b for b in BUTTON_DEFINITIONS if b["key"] == btn_key), None)
        target_name = target_def["name"] if target_def else btn_key

        for k, btn in record_buttons.items():
            if k == btn_key:
                btn.icon = ft.Icons.KEYBOARD_OUTLINED
                btn.icon_color = ft.Colors.AMBER_400
                btn.tooltip = "Listening... Press any key"
            else:
                btn.icon = ft.Icons.KEYBOARD
                btn.icon_color = None
                btn.tooltip = "Press a key on keyboard to remap"

        status_text.value = f"Listening for key press for {target_name}... Press any key on your keyboard."
        status_text.color = ft.Colors.AMBER_300
        page.update()

    def stop_listening():
        nonlocal listening_target
        listening_target = None
        for btn in record_buttons.values():
            btn.icon = ft.Icons.KEYBOARD
            btn.icon_color = None
            btn.tooltip = "Press a key on keyboard to remap"
        status_text.value = "Button mapping updated. Click Continue to proceed to camera view."
        status_text.color = ft.Colors.GREY_400
        page.update()

    def on_keyboard_event(e: ft.KeyboardEvent):
        nonlocal listening_target
        if not listening_target:
            return

        key_name = normalize_flet_key(e.key)
        if not key_name:
            return

        dd = dropdowns.get(listening_target)
        if dd:
            # Ensure key_name is present in the dropdown options
            if not any(opt.key == key_name for opt in dd.options):
                dd.options.append(ft.dropdown.Option(key_name))
            dd.value = key_name

        stop_listening()

    page.on_keyboard_event = on_keyboard_event

    def build_button_row(btn_def: dict[str, str]):
        btn_key = btn_def["key"]
        current_val = saved_config.get(btn_key, btn_def["default"])

        # Make sure current_val exists in options
        options = [ft.dropdown.Option(opt) for opt in AVAILABLE_ACTIONS]
        if not any(opt.key == current_val for opt in options):
            options.append(ft.dropdown.Option(current_val))

        dd = ft.Dropdown(
            options=options,
            value=current_val,
            width=200,
            content_padding=10,
        )
        dropdowns[btn_key] = dd

        rec_btn = ft.IconButton(
            icon=ft.Icons.KEYBOARD,
            tooltip="Press a key on keyboard to remap",
            on_click=lambda e, k=btn_key: start_listening(k),
        )
        record_buttons[btn_key] = rec_btn

        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(btn_def["name"], size=16, weight=ft.FontWeight.W_600),
                            ft.Text(btn_def["desc"], size=12, color=ft.Colors.GREY_500),
                        ],
                        expand=True,
                    ),
                    ft.Row(
                        [
                            dd,
                            rec_btn,
                        ],
                        alignment=ft.MainAxisAlignment.END,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=16, vertical=10),
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=8,
            margin=ft.Margin.only(bottom=8),
        )

    button_controls = [build_button_row(b) for b in BUTTON_DEFINITIONS]

    def on_reset(e):
        nonlocal listening_target
        listening_target = None
        for b in BUTTON_DEFINITIONS:
            btn_key = b["key"]
            default_val = DEFAULT_BUTTON_MAPPINGS.get(btn_key, b["default"])
            if btn_key in dropdowns:
                dropdowns[btn_key].value = default_val
        stop_listening()

    def on_submit(e):
        """Save remapped buttons to config.ini and navigate to camera feed."""
        for b in BUTTON_DEFINITIONS:
            btn_key = b["key"]
            if btn_key in dropdowns and dropdowns[btn_key].value:
                save_setting("Buttons", btn_key, dropdowns[btn_key].value)

        # Clear keyboard listener before navigation
        page.on_keyboard_event = None

        from flet_app.screens.camera_feed import camera_feed_page
        camera_feed_page(page)

    def on_back(e):
        """Navigate back to Step 2: Camera flip options."""
        page.on_keyboard_event = None
        from flet_app.screens.camera_flip_options import camera_flip_options_page
        camera_flip_options_page(page)

    page.add(
        ft.SafeArea(
            expand=True,
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.Icons.ARROW_BACK,
                                    on_click=on_back,
                                    tooltip="Back to Camera Flip",
                                ),
                                ft.Text("Button Mapping", size=26, weight=ft.FontWeight.BOLD),
                                ft.Container(width=40),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        status_text,
                        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                        ft.Column(
                            controls=button_controls,
                            spacing=4,
                        ),
                        ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                        ft.Row(
                            [
                                ft.OutlinedButton(
                                    content=ft.Text("Reset Defaults"),
                                    icon=ft.Icons.RESTORE,
                                    on_click=on_reset,
                                ),
                                ft.FilledButton(
                                    content=ft.Text("Continue to Camera View"),
                                    icon=ft.Icons.ARROW_FORWARD,
                                    on_click=on_submit,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=16,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=20,
            ),
        )
    )
