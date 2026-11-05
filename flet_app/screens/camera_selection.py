import flet as ft
from core.camera import list_cameras
from core.config import get_camera_config, save_setting

# Global variable to store selected camera index, initialized from config
selected_camera_index = get_camera_config()["selected_camera_index"]


def refresh_cameras():
    return list_cameras()


def camera_selection_page(page: ft.Page):
    global selected_camera_index

    page.clean()
    page.title = "Webcam Railgun - Camera Selection"
    page.window.width = 800
    page.window.height = 600

    def build_camera_list():
        cameras = refresh_cameras()
        radio_controls = []

        for i, name in enumerate(cameras):
            radio_controls.append(
                ft.Radio(
                    value=str(i),
                    label=f"Camera {i}: {name}"
                )
            )

        return cameras, radio_controls

    cameras, radio_controls = build_camera_list()

    # Restore previously selected camera index if valid
    saved_index_str = str(selected_camera_index)
    valid_saved = any(rc.value == saved_index_str for rc in radio_controls)
    initial_value = saved_index_str if valid_saved else ("0" if cameras else None)

    radio_group = ft.RadioGroup(
        content=ft.Column(
            controls=radio_controls,
            spacing=10
        ),
        value=initial_value
    )

    subtitle_text = ft.Text(
        f"Select a camera to use for screen detection (Total: {len(cameras)}).",
        size=14,
        color=ft.Colors.GREY_400,
    )

    def on_refresh(e):
        nonlocal cameras, radio_controls
        cameras, radio_controls = build_camera_list()
        radio_group.content.controls = radio_controls
        valid_selection = any(rc.value == radio_group.value for rc in radio_controls)
        radio_group.value = radio_group.value if valid_selection else ("0" if cameras else None)
        subtitle_text.value = f"Select a camera to use for screen detection (Total: {len(cameras)})."
        page.update()

    def on_submit(e):
        global selected_camera_index
        if radio_group.value is not None:
            selected_camera_index = int(radio_group.value)
            save_setting("Camera", "selected_camera_index", selected_camera_index)
        from flet_app.screens.camera_flip_options import camera_flip_options_page
        camera_flip_options_page(page)

    def on_back(e):
        from flet_app.screens.welcome import welcome_page
        welcome_page(page)

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
                                    tooltip="Back to Welcome",
                                ),
                                ft.Text("Step 1: Camera Selection", size=26, weight=ft.FontWeight.BOLD),
                                ft.IconButton(
                                    icon=ft.Icons.REFRESH,
                                    on_click=on_refresh,
                                    tooltip="Refresh camera list",
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        subtitle_text,
                        ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                        radio_group,
                        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                        ft.FilledButton(
                            content=ft.Text("Continue"),
                            icon=ft.Icons.ARROW_FORWARD,
                            on_click=on_submit,
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=20,
            )
        )
    )
