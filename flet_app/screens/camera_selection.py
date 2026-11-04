import flet as ft
from core.camera import list_cameras

# Global variable to store selected camera index
selected_camera_index = 0


def refresh_cameras():
    """Get list of available cameras."""
    return list_cameras()


def camera_selection_page(page: ft.Page):
    """Camera selection screen with refresh button."""
    global selected_camera_index

    page.clean()
    page.title = "Webcam Railgun - Camera Selection"

    def build_camera_list():
        """Build radio controls for available cameras."""
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

    radio_group = ft.RadioGroup(
        content=ft.Column(
            controls=radio_controls,
            spacing=10
        ),
        value="0" if cameras else None
    )

    def on_refresh(e):
        """Refresh camera list."""
        nonlocal cameras, radio_controls
        cameras, radio_controls = build_camera_list()
        radio_group.content.controls = radio_controls
        radio_group.value = "0" if cameras else None
        page.update()

    def on_submit(e):
        """Navigate to camera flip options page."""
        global selected_camera_index
        selected_camera_index = int(radio_group.value)
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
                                ft.Text("Camera Selection", size=30),
                                ft.IconButton(
                                    icon=ft.Icons.REFRESH,
                                    on_click=on_refresh,
                                    tooltip="Refresh camera list"
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Text(f"Please select a camera to continue (Total: {len(cameras)})", size=20),
                        radio_group,
                        ft.FilledButton(
                            content=ft.Text("Continue"),
                            on_click=on_submit
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                )
            )
        )
    )
