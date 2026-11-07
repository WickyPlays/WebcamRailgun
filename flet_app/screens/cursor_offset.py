import flet as ft
from core.config import get_cursor_config, save_setting

def cursor_offset_page(page: ft.Page):
    page.clean()
    page.title = "Webcam Railgun - Cursor Offset"
    page.window.width = 800
    page.window.height = 650

    saved_cursor_config = get_cursor_config()
    current_x = saved_cursor_config.get("offset_x", 0)
    current_y = saved_cursor_config.get("offset_y", 0)

    def parse_int_safe(val: str, default: int = 0) -> int:
        try:
            return int(val.strip())
        except (ValueError, TypeError, AttributeError):
            return default

    # Text fields for displaying and manually typing offsets
    x_input = ft.TextField(
        value=str(current_x),
        width=100,
        text_align=ft.TextAlign.CENTER,
        text_size=18,
        dense=True,
        keyboard_type=ft.KeyboardType.NUMBER,
    )

    y_input = ft.TextField(
        value=str(current_y),
        width=100,
        text_align=ft.TextAlign.CENTER,
        text_size=18,
        dense=True,
        keyboard_type=ft.KeyboardType.NUMBER,
    )

    def set_x(new_val: int):
        nonlocal current_x
        current_x = new_val
        x_input.value = str(current_x)
        x_input.update()

    def set_y(new_val: int):
        nonlocal current_y
        current_y = new_val
        y_input.value = str(current_y)
        y_input.update()

    def adjust_x(delta: int):
        val = parse_int_safe(x_input.value, current_x)
        set_x(val + delta)

    def adjust_y(delta: int):
        val = parse_int_safe(y_input.value, current_y)
        set_y(val + delta)

    def on_x_change(e):
        nonlocal current_x
        current_x = parse_int_safe(x_input.value, 0)

    def on_y_change(e):
        nonlocal current_y
        current_y = parse_int_safe(y_input.value, 0)

    x_input.on_change = on_x_change
    y_input.on_change = on_y_change

    def on_reset(e):
        set_x(0)
        set_y(0)

    def on_submit(e):
        """Save offset settings and navigate to button mapping."""
        final_x = parse_int_safe(x_input.value, 0)
        final_y = parse_int_safe(y_input.value, 0)

        save_setting("Cursor", "offset_x", final_x)
        save_setting("Cursor", "offset_y", final_y)

        from flet_app.screens.button_mapping import button_mapping_page
        button_mapping_page(page)

    def on_back(e):
        """Navigate back to Step 2: Camera flip options."""
        from flet_app.screens.camera_flip_options import camera_flip_options_page
        camera_flip_options_page(page)

    # Offset X control block
    x_stepper = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.SWAP_HORIZ, size=22, color=ft.Colors.BLUE_400),
                        ft.Text("Cursor Offset X (Horizontal)", size=16, weight=ft.FontWeight.BOLD),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text(
                    "Negative (-) shifts left, Positive (+) shifts right.",
                    size=12,
                    color=ft.Colors.GREY_400,
                ),
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.REMOVE,
                            tooltip="Decrease Offset X by 10 (-10)",
                            icon_size=24,
                            on_click=lambda _: adjust_x(-10),
                        ),
                        x_input,
                        ft.IconButton(
                            icon=ft.Icons.ADD,
                            tooltip="Increase Offset X by 10 (+10)",
                            icon_size=24,
                            on_click=lambda _: adjust_x(10),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        ft.OutlinedButton("-10", on_click=lambda _: adjust_x(-10)),
                        ft.OutlinedButton("-1", on_click=lambda _: adjust_x(-1)),
                        ft.OutlinedButton("0", on_click=lambda _: set_x(0)),
                        ft.OutlinedButton("+1", on_click=lambda _: adjust_x(1)),
                        ft.OutlinedButton("+10", on_click=lambda _: adjust_x(10)),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=6,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        bgcolor=ft.Colors.WHITE_10,
        border_radius=10,
        padding=16,
        width=520,
    )

    # Offset Y control block
    y_stepper = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.SWAP_VERT, size=22, color=ft.Colors.GREEN_400),
                        ft.Text("Cursor Offset Y (Vertical)", size=16, weight=ft.FontWeight.BOLD),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text(
                    "Negative (-) shifts up, Positive (+) shifts down.",
                    size=12,
                    color=ft.Colors.GREY_400,
                ),
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.REMOVE,
                            tooltip="Decrease Offset Y by 10 (-10)",
                            icon_size=24,
                            on_click=lambda _: adjust_y(-10),
                        ),
                        y_input,
                        ft.IconButton(
                            icon=ft.Icons.ADD,
                            tooltip="Increase Offset Y by 10 (+10)",
                            icon_size=24,
                            on_click=lambda _: adjust_y(10),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        ft.OutlinedButton("-10", on_click=lambda _: adjust_y(-10)),
                        ft.OutlinedButton("-1", on_click=lambda _: adjust_y(-1)),
                        ft.OutlinedButton("0", on_click=lambda _: set_y(0)),
                        ft.OutlinedButton("+1", on_click=lambda _: adjust_y(1)),
                        ft.OutlinedButton("+10", on_click=lambda _: adjust_y(10)),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=6,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        bgcolor=ft.Colors.WHITE_10,
        border_radius=10,
        padding=16,
        width=520,
    )

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
                                ft.Text("Step 3: Cursor Offset", size=26, weight=ft.FontWeight.BOLD),
                                ft.Container(width=40),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Text(
                            "Calibrate cursor position relative to screen detection (step ±10).",
                            size=14,
                            color=ft.Colors.GREY_400,
                        ),
                        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                        x_stepper,
                        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                        y_stepper,
                        ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                        ft.Row(
                            [
                                ft.OutlinedButton(
                                    content=ft.Text("Reset Defaults"),
                                    icon=ft.Icons.RESTORE,
                                    on_click=on_reset,
                                ),
                                ft.FilledButton(
                                    content=ft.Text("Continue"),
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
                alignment=ft.Alignment.CENTER,
            ),
        )
    )
