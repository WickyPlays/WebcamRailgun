import flet as ft
from core.config import (
    DEFAULT_CONFIG,
    get_border_config,
    get_buttons_config,
    get_camera_config,
    get_cursor_config,
    get_detection_config,
    get_gun_config,
    get_view_config,
    save_setting,
)
from core.gun_input import AVAILABLE_ACTIONS, BUTTON_DEFINITIONS, list_serial_ports
from flet_app.screens.button_mapping import normalize_flet_key


def _parse_int(val: str | None, default: int, min_val: int | None = None, max_val: int | None = None) -> int:
    try:
        parsed = int((val or "").strip())
    except (ValueError, TypeError):
        parsed = default
    if min_val is not None:
        parsed = max(min_val, parsed)
    if max_val is not None:
        parsed = min(max_val, parsed)
    return parsed


def _flip_flags_from_choice(choice: str) -> tuple[bool, bool]:
    if choice == "horizontal":
        return True, False
    if choice == "vertical":
        return False, True
    if choice == "both":
        return True, True
    return False, False


def settings_page(page: ft.Page):
    page.clean()
    page.title = "Webcam Railgun - Settings"
    page.window.full_screen = False
    page.window.width = 960
    page.window.height = 700

    cam_cfg = get_camera_config()
    cursor_cfg = get_cursor_config()
    det_cfg = get_detection_config()
    border_cfg = get_border_config()
    view_cfg = get_view_config()
    gun_cfg = get_gun_config()
    btn_cfg = get_buttons_config()

    flip_choice = cam_cfg.get("flip_choice", "none")
    if flip_choice not in {"none", "horizontal", "vertical", "both"}:
        fh = cam_cfg.get("flip_horizontal", False)
        fv = cam_cfg.get("flip_vertical", False)
        if fh and fv:
            flip_choice = "both"
        elif fh:
            flip_choice = "horizontal"
        elif fv:
            flip_choice = "vertical"
        else:
            flip_choice = "none"

    flip_dropdown = ft.Dropdown(
        label="Camera Orientation Flip",
        value=flip_choice,
        width=280,
        dense=True,
        options=[
            ft.dropdown.Option(key="none", text="No flip (default)"),
            ft.dropdown.Option(key="horizontal", text="Flip horizontally"),
            ft.dropdown.Option(key="vertical", text="Flip vertically"),
            ft.dropdown.Option(key="both", text="Flip both horizontally and vertically"),
        ],
    )

    cam_visible_switch = ft.Switch(
        label="Show Camera Feed",
        value=bool(view_cfg.get("cam_visible", True)),
    )
    mask_visible_switch = ft.Switch(
        label="Show Detection Mask",
        value=bool(view_cfg.get("mask_visible", True)),
    )
    views_flipped_switch = ft.Switch(
        label="Flip Views Layout",
        value=bool(view_cfg.get("views_flipped", False)),
    )

    offset_x_field = ft.TextField(
        label="Offset X (px)",
        value=str(cursor_cfg.get("offset_x", 0)),
        width=160,
        dense=True,
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    offset_y_field = ft.TextField(
        label="Offset Y (px)",
        value=str(cursor_cfg.get("offset_y", 0)),
        width=160,
        dense=True,
        keyboard_type=ft.KeyboardType.NUMBER,
    )

    initial_tolerance = max(0, min(255, int(det_cfg.get("color_tolerance", 60))))
    tolerance_value_text = ft.Text(str(initial_tolerance), size=14, weight=ft.FontWeight.BOLD, width=40)

    def on_tolerance_change(e):
        tolerance_value_text.value = str(int(e.control.value))
        tolerance_value_text.update()

    tolerance_slider = ft.Slider(
        min=0,
        max=255,
        divisions=255,
        value=initial_tolerance,
        label="{value}",
        expand=True,
        on_change=on_tolerance_change,
    )

    initial_thickness = max(1, min(200, int(border_cfg.get("thickness", 10))))
    thickness_value_text = ft.Text(f"{initial_thickness} px", size=14, weight=ft.FontWeight.BOLD, width=55)

    def on_thickness_change(e):
        thickness_value_text.value = f"{int(e.control.value)} px"
        thickness_value_text.update()

    thickness_slider = ft.Slider(
        min=1,
        max=200,
        divisions=199,
        value=initial_thickness,
        label="{value}",
        expand=True,
        on_change=on_thickness_change,
    )

    gun_enabled_switch = ft.Switch(
        label="Enable Gun Controller",
        value=bool(gun_cfg.get("enabled", True)),
    )
    offscreen_reload_switch = ft.Switch(
        label="Offscreen Reload",
        value=bool(gun_cfg.get("offscreen_reload", False)),
    )

    def build_port_options(selected_port: str) -> list[ft.dropdown.Option]:
        opts = [ft.dropdown.Option(key="AUTO", text="AUTO (Auto-detect)")]
        detected = list_serial_ports()
        seen = {"AUTO"}
        for device, desc in detected:
            seen.add(device)
            label = f"{device} - {desc}" if desc else device
            opts.append(ft.dropdown.Option(key=device, text=label))
        if selected_port and selected_port not in seen:
            opts.append(ft.dropdown.Option(key=selected_port, text=f"{selected_port} (Saved)"))
        return opts

    saved_port = str(gun_cfg.get("port", "AUTO"))
    port_dropdown = ft.Dropdown(
        label="Serial Port",
        value=saved_port,
        options=build_port_options(saved_port),
        width=280,
        dense=True,
    )

    def on_refresh_ports(e):
        current_val = port_dropdown.value or "AUTO"
        port_dropdown.options = build_port_options(current_val)
        port_dropdown.value = current_val
        port_dropdown.update()

    standard_baudrates = ["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]
    saved_baud = str(gun_cfg.get("baudrate", 115200))
    if saved_baud not in standard_baudrates:
        standard_baudrates.append(saved_baud)

    baudrate_dropdown = ft.Dropdown(
        label="Baudrate",
        value=saved_baud,
        options=[ft.dropdown.Option(key=b, text=b) for b in standard_baudrates],
        width=180,
        dense=True,
    )

    listening_target: str | None = None
    button_dropdowns: dict[str, ft.Dropdown] = {}
    record_buttons: dict[str, ft.IconButton] = {}

    def start_listening(btn_key: str):
        nonlocal listening_target
        listening_target = btn_key
        for k, btn in record_buttons.items():
            if k == btn_key:
                btn.icon = ft.Icons.KEYBOARD_OUTLINED
                btn.icon_color = ft.Colors.AMBER_400
                btn.tooltip = "Listening... Press any key"
            else:
                btn.icon = ft.Icons.KEYBOARD
                btn.icon_color = None
                btn.tooltip = "Press a key on keyboard to remap"
        page.update()

    def stop_listening():
        nonlocal listening_target
        listening_target = None
        for btn in record_buttons.values():
            btn.icon = ft.Icons.KEYBOARD
            btn.icon_color = None
            btn.tooltip = "Press a key on keyboard to remap"
        page.update()

    def on_keyboard_event(e: ft.KeyboardEvent):
        if not listening_target:
            return
        key_name = normalize_flet_key(e.key)
        if not key_name:
            return
        dd = button_dropdowns.get(listening_target)
        if dd:
            if not any(opt.key == key_name for opt in dd.options):
                dd.options.append(ft.dropdown.Option(key_name))
            dd.value = key_name
        stop_listening()

    page.on_keyboard_event = on_keyboard_event

    button_rows: list[ft.Control] = []
    for btn_def in BUTTON_DEFINITIONS:
        btn_key = btn_def["key"]
        current_val = btn_cfg.get(btn_key, btn_def["default"])
        options = [ft.dropdown.Option(opt) for opt in AVAILABLE_ACTIONS]
        if not any(opt.key == current_val for opt in options):
            options.append(ft.dropdown.Option(current_val))

        dd = ft.Dropdown(
            options=options,
            value=current_val,
            width=220,
            dense=True,
            text_size=13,
        )
        button_dropdowns[btn_key] = dd

        rec_btn = ft.IconButton(
            icon=ft.Icons.KEYBOARD,
            tooltip="Press a key on keyboard to remap",
            on_click=lambda e, k=btn_key: start_listening(k),
        )
        record_buttons[btn_key] = rec_btn

        button_rows.append(
            ft.Row(
                [
                    ft.Text(btn_def["name"], size=13, expand=True),
                    dd,
                    rec_btn,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

    def section_card(title: str, icon: str, controls: list[ft.Control]) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(icon, size=18, color=ft.Colors.AMBER_400),
                            ft.Text(title, size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400),
                        ],
                        spacing=8,
                    ),
                    ft.Divider(height=6, color=ft.Colors.WHITE_24),
                    *controls,
                ],
                spacing=10,
            ),
            bgcolor=ft.Colors.WHITE_10,
            border_radius=3,
            padding=16,
        )

    def show_snackbar(message: str, bgcolor: str = ft.Colors.GREEN_700):
        page.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor=bgcolor)
        page.snack_bar.open = True
        page.update()

    def on_reset_defaults(e):
        flip_dropdown.value = DEFAULT_CONFIG["Camera"]["flip_choice"]
        cam_visible_switch.value = DEFAULT_CONFIG["View"]["cam_visible"] == "True"
        mask_visible_switch.value = DEFAULT_CONFIG["View"]["mask_visible"] == "True"
        views_flipped_switch.value = DEFAULT_CONFIG["View"]["views_flipped"] == "True"

        offset_x_field.value = DEFAULT_CONFIG["Cursor"]["offset_x"]
        offset_y_field.value = DEFAULT_CONFIG["Cursor"]["offset_y"]

        default_tol = int(DEFAULT_CONFIG["Detection"]["color_tolerance"])
        tolerance_slider.value = default_tol
        tolerance_value_text.value = str(default_tol)

        default_thick = int(DEFAULT_CONFIG["Border"]["thickness"])
        thickness_slider.value = default_thick
        thickness_value_text.value = f"{default_thick} px"

        gun_enabled_switch.value = DEFAULT_CONFIG["Gun"]["enabled"] == "True"
        offscreen_reload_switch.value = DEFAULT_CONFIG["Gun"]["offscreen_reload"] == "True"
        port_dropdown.value = DEFAULT_CONFIG["Gun"]["port"]
        baudrate_dropdown.value = DEFAULT_CONFIG["Gun"]["baudrate"]

        for btn_key, dd in button_dropdowns.items():
            dd.value = DEFAULT_CONFIG["Buttons"][btn_key]

        show_snackbar("Defaults loaded. Click Save to apply.", ft.Colors.BLUE_700)

    def on_save(e):
        chosen_flip = flip_dropdown.value or "none"
        fh, fv = _flip_flags_from_choice(chosen_flip)
        save_setting("Camera", "flip_choice", chosen_flip)
        save_setting("Camera", "flip_horizontal", fh)
        save_setting("Camera", "flip_vertical", fv)

        save_setting("View", "cam_visible", bool(cam_visible_switch.value))
        save_setting("View", "mask_visible", bool(mask_visible_switch.value))
        save_setting("View", "views_flipped", bool(views_flipped_switch.value))

        ox = _parse_int(offset_x_field.value, 0)
        oy = _parse_int(offset_y_field.value, 0)
        offset_x_field.value = str(ox)
        offset_y_field.value = str(oy)
        save_setting("Cursor", "offset_x", ox)
        save_setting("Cursor", "offset_y", oy)

        tol = int(tolerance_slider.value or 60)
        save_setting("Detection", "color_tolerance", tol)

        thick = int(thickness_slider.value or 10)
        save_setting("Border", "thickness", thick)

        save_setting("Gun", "enabled", bool(gun_enabled_switch.value))
        save_setting("Gun", "offscreen_reload", bool(offscreen_reload_switch.value))
        save_setting("Gun", "port", port_dropdown.value or "AUTO")
        save_setting("Gun", "baudrate", _parse_int(baudrate_dropdown.value, 115200, min_val=1))

        for btn_key, dd in button_dropdowns.items():
            if dd.value:
                save_setting("Buttons", btn_key, dd.value)

        show_snackbar("Settings saved to config.ini.")

    def on_back(e):
        page.on_keyboard_event = None
        from flet_app.screens.welcome import welcome_page
        welcome_page(page)

    header = ft.Row(
        [
            ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        tooltip="Back to Welcome",
                        on_click=on_back,
                    ),
                    ft.Text("Settings", size=24, weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Row(
                [
                    ft.OutlinedButton(
                        content=ft.Row(
                            [ft.Icon(ft.Icons.RESTORE, size=18), ft.Text("Reset Defaults")],
                            spacing=6,
                        ),
                        on_click=on_reset_defaults,
                    ),
                    ft.FilledButton(
                        content=ft.Row(
                            [ft.Icon(ft.Icons.SAVE, size=18), ft.Text("Save")],
                            spacing=6,
                        ),
                        on_click=on_save,
                    ),
                ],
                spacing=10,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    body = ft.Column(
        [
            ft.Row(
                [
                    ft.Container(
                        content=section_card(
                            "Camera Orientation",
                            ft.Icons.FLIP,
                            [flip_dropdown],
                        ),
                        expand=True,
                    ),
                    ft.Container(
                        content=section_card(
                            "View",
                            ft.Icons.VISIBILITY,
                            [
                                cam_visible_switch,
                                mask_visible_switch,
                                views_flipped_switch,
                            ],
                        ),
                        expand=True,
                    ),
                ],
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            ft.Row(
                [
                    ft.Container(
                        content=section_card(
                            "Cursor Calibration",
                            ft.Icons.MY_LOCATION,
                            [
                                ft.Row(
                                    [offset_x_field, offset_y_field],
                                    spacing=12,
                                ),
                            ],
                        ),
                        expand=True,
                    ),
                    ft.Container(
                        content=section_card(
                            "Detection & Border",
                            ft.Icons.COLOR_LENS,
                            [
                                ft.Row(
                                    [
                                        ft.Text("Color Tolerance", size=13, width=130),
                                        tolerance_slider,
                                        tolerance_value_text,
                                    ],
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ft.Row(
                                    [
                                        ft.Text("Border Thickness", size=13, width=130),
                                        thickness_slider,
                                        thickness_value_text,
                                    ],
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ],
                        ),
                        expand=True,
                    ),
                ],
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            section_card(
                "Gun Controller",
                ft.Icons.MEMORY,
                [
                    ft.Row(
                        [gun_enabled_switch, offscreen_reload_switch],
                        spacing=24,
                    ),
                    ft.Row(
                        [
                            port_dropdown,
                            ft.IconButton(
                                icon=ft.Icons.REFRESH,
                                tooltip="Refresh serial ports",
                                on_click=on_refresh_ports,
                            ),
                            baudrate_dropdown,
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
            ),
            section_card(
                "Button Mappings",
                ft.Icons.GAMEPAD,
                button_rows,
            ),
        ],
        spacing=16,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    page.add(
        ft.SafeArea(
            expand=True,
            content=ft.Container(
                content=ft.Column(
                    [
                        header,
                        ft.Divider(height=8, color=ft.Colors.WHITE_12),
                        body,
                    ],
                    spacing=8,
                    expand=True,
                ),
                padding=20,
                expand=True,
            ),
        )
    )
