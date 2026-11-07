import flet as ft
from core.camera import list_cameras
from core.config import (
    get_buttons_config,
    get_camera_config,
    get_cursor_config,
    get_detection_config,
    get_gun_config,
    get_view_config,
    save_setting,
)

def welcome_page(page: ft.Page):
    page.clean()
    page.title = "Webcam Railgun - Welcome"
    page.window.full_screen = False
    page.window.width = 960
    page.window.height = 700

    # Load all current configs from config.ini
    cam_cfg = get_camera_config()
    cursor_cfg = get_cursor_config()
    det_cfg = get_detection_config()
    gun_cfg = get_gun_config()
    btn_cfg = get_buttons_config()
    view_cfg = get_view_config()

    saved_camera_index = cam_cfg.get("selected_camera_index", 0)

    # Detect cameras
    cameras = list_cameras()

    def build_camera_options():
        if not cameras:
            return [ft.dropdown.Option(key="", text="No cameras detected")]
        return [
            ft.dropdown.Option(
                key=str(i),
                text=f"Camera {i}: {name}"
            )
            for i, name in enumerate(cameras)
        ]

    options = build_camera_options()
    valid_saved = any(opt.key == str(saved_camera_index) for opt in options if opt.key != "")
    initial_camera_value = str(saved_camera_index) if valid_saved else ("0" if cameras else "")

    camera_dropdown = ft.Dropdown(
        options=options,
        value=initial_camera_value,
        width=300,
        dense=True,
        text_size=13,
        label="Target Camera",
        hint_text="Select a camera",
    )

    def on_refresh_cameras(e):
        nonlocal cameras
        cameras = list_cameras()
        new_opts = build_camera_options()
        camera_dropdown.options = new_opts
        is_valid = any(opt.key == camera_dropdown.value for opt in new_opts if opt.key != "")
        camera_dropdown.value = camera_dropdown.value if is_valid else ("0" if cameras else "")
        update_camera_summary()
        page.update()

    def on_continue_with_configured(e):
        if not camera_dropdown.value or not cameras:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Please connect a camera and select it first!"),
                bgcolor=ft.Colors.RED_700,
            )
            page.snack_bar.open = True
            page.update()
            return

        selected_idx = int(camera_dropdown.value)
        save_setting("Camera", "selected_camera_index", selected_idx)

        from flet_app.screens.camera_feed import camera_feed_page
        camera_feed_page(page, from_welcome=True)

    def on_start_test(e):
        if camera_dropdown.value:
            try:
                save_setting("Camera", "selected_camera_index", int(camera_dropdown.value))
            except Exception:
                pass
        from flet_app.screens.camera_selection import camera_selection_page
        camera_selection_page(page)

    def on_test_gun(e):
        from test.test_gun import gun_test_page

        def return_to_welcome():
            welcome_page(page)

        gun_test_page(page, on_exit=return_to_welcome)

    # --- Config Summary Helpers ---
    def config_row(label: str, value: str, icon: str | None = None) -> ft.Container:
        return ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.Icon(icon, size=15, color=ft.Colors.BLUE_200) if icon else ft.Container(width=15),
                            ft.Text(label, size=13, color=ft.Colors.GREY_300),
                        ],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text(value, size=13, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(vertical=2),
        )

    def section_header(title: str, icon: str) -> ft.Container:
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, size=16, color=ft.Colors.AMBER_400),
                    ft.Text(title, size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.only(top=6, bottom=2),
        )

    # Camera summary text widget to dynamically reflect dropdown changes
    camera_summary_text = ft.Text(
        f"Camera {initial_camera_value}" if initial_camera_value else "None",
        size=13,
        weight=ft.FontWeight.W_600,
        color=ft.Colors.WHITE,
    )

    def update_camera_summary():
        val = camera_dropdown.value
        if val != "":
            name = cameras[int(val)] if (cameras and int(val) < len(cameras)) else ""
            display_name = f"Camera {val} ({name[:18]}...)" if len(name) > 18 else f"Camera {val}"
            camera_summary_text.value = display_name
        else:
            camera_summary_text.value = "None"
        camera_summary_text.update()

    def on_dropdown_change(e):
        update_camera_summary()

    camera_dropdown.on_change = on_dropdown_change

    flip_choice_str = cam_cfg.get("flip_choice", "none").capitalize()
    if flip_choice_str == "Both":
        flip_choice_str = "Horizontal & Vertical"

    cam_vis_str = "Shown" if view_cfg.get("cam_visible", True) else "Hidden"
    mask_vis_str = "Shown" if view_cfg.get("mask_visible", True) else "Hidden"

    gun_enabled_str = "Enabled" if gun_cfg.get("enabled", True) else "Disabled"
    offscreen_str = "Enabled" if gun_cfg.get("offscreen_reload", False) else "Disabled"

    # Configured display settings
    right_panel = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.DISPLAY_SETTINGS, color=ft.Colors.AMBER_400, size=20),
                        ft.Text("Pre-configured Settings", size=16, weight=ft.FontWeight.BOLD),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Divider(height=8, color=ft.Colors.WHITE_24),
                # 1. Camera & View
                section_header("Camera & View", ft.Icons.VIDEOCAM),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.CAMERA_ALT, size=15, color=ft.Colors.BLUE_200),
                                    ft.Text("Target Camera", size=13, color=ft.Colors.GREY_300),
                                ],
                                spacing=6,
                            ),
                            camera_summary_text,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=ft.Padding.symmetric(vertical=2),
                ),
                config_row("Orientation Flip", flip_choice_str, ft.Icons.FLIP),
                config_row("Views Visibility", f"Cam: {cam_vis_str} | Mask: {mask_vis_str}", ft.Icons.VISIBILITY),

                # 2. Cursor Calibration
                section_header("Cursor Calibration", ft.Icons.MY_LOCATION),
                config_row("Offset X (Horizontal)", f"{cursor_cfg.get('offset_x', 0):+d} px", ft.Icons.SWAP_HORIZ),
                config_row("Offset Y (Vertical)", f"{cursor_cfg.get('offset_y', 0):+d} px", ft.Icons.SWAP_VERT),

                # 3. Detection
                section_header("Screen Detection", ft.Icons.COLOR_LENS),
                config_row("Color Tolerance", str(det_cfg.get("color_tolerance", 60)), ft.Icons.PALETTE),

                # 4. Gun Controller
                section_header("Gun Controller", ft.Icons.MEMORY),
                config_row("Serial Port", f"{gun_cfg.get('port', 'AUTO')} ({gun_cfg.get('baudrate', 115200)} baud)", ft.Icons.USB),
                config_row("Gun Status", gun_enabled_str, ft.Icons.POWER_SETTINGS_NEW),
                config_row("Offscreen Reload", offscreen_str, ft.Icons.REDO),

                # 5. Button Mappings
                section_header("Gun Buttons Mapping", ft.Icons.GAMEPAD),
                config_row("Trigger (Main)", btn_cfg.get("trigger", "Left Click"), ft.Icons.ADS_CLICK),
                config_row("Secondary (Button)", btn_cfg.get("secondary", "Right Click"), ft.Icons.TOUCH_APP),
                config_row("Custom Button A (btnexA)", btn_cfg.get("btnexA", "R"), ft.Icons.RADIO_BUTTON_CHECKED),
                config_row("Custom Button B (btnexB)", btn_cfg.get("btnexB", "Shift"), ft.Icons.RADIO_BUTTON_CHECKED),
                config_row("Custom Button C (btnexC)", btn_cfg.get("btnexC", "Escape"), ft.Icons.RADIO_BUTTON_CHECKED),
            ],
            spacing=3,
            scroll=ft.ScrollMode.AUTO,
        ),
        bgcolor=ft.Colors.WHITE_10,
        border_radius=12,
        padding=16,
        width=430,
        height=540,
    )

    left_panel = ft.Container(
        content=ft.Column(
            [
                ft.Image(
                    src="/gun_icon.png",
                    width=100,
                    height=100,
                    fit=ft.BoxFit.CONTAIN,
                ),
                ft.Text(
                    "Webcam Railgun",
                    size=30,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "A mini project made by Wicky",
                    size=14,
                    color=ft.Colors.GREY_400,
                ),
                ft.Divider(height=12, color=ft.Colors.TRANSPARENT),

                ft.Row(
                    [
                        camera_dropdown,
                        ft.IconButton(
                            icon=ft.Icons.REFRESH,
                            tooltip="Refresh camera list",
                            on_click=on_refresh_cameras,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                ),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),

                ft.FilledButton(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.PLAY_ARROW, size=22),
                            ft.Text("Continue with configured settings", size=14, weight=ft.FontWeight.BOLD),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    width=340,
                    height=48,
                    on_click=on_continue_with_configured,
                ),
                ft.OutlinedButton(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.TUNE, size=18),
                            ft.Text("Start test (Setup Wizard)", size=14, weight=ft.FontWeight.W_600),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    width=340,
                    height=44,
                    on_click=on_start_test,
                ),
                ft.OutlinedButton(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.SPORTS_ESPORTS, size=18),
                            ft.Text("Test gun", size=14, weight=ft.FontWeight.W_600),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    width=340,
                    height=44,
                    on_click=on_test_gun,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        width=430,
        height=540,
        alignment=ft.Alignment.CENTER,
    )

    page.add(
        ft.SafeArea(
            expand=True,
            content=ft.Container(
                content=ft.Row(
                    [
                        left_panel,
                        ft.VerticalDivider(width=20, color=ft.Colors.WHITE_12),
                        right_panel,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=16,
                ),
                alignment=ft.Alignment.CENTER,
                padding=16,
            ),
        )
    )
