import flet as ft
from core.config import get_camera_config, save_setting

# Global variables to store flip options, initialized from config
_saved_camera_config = get_camera_config()
flip_horizontal = _saved_camera_config["flip_horizontal"]
flip_vertical = _saved_camera_config["flip_vertical"]


def _get_current_choice() -> str:
    """Determine the radio option string corresponding to current flip settings."""
    cfg_choice = get_camera_config().get("flip_choice")
    if cfg_choice in {"horizontal", "vertical", "both", "none"}:
        return cfg_choice

    if flip_horizontal and flip_vertical:
        return "both"
    elif flip_horizontal:
        return "horizontal"
    elif flip_vertical:
        return "vertical"
    return "none"


def camera_flip_options_page(page: ft.Page):
    """Camera flip options screen."""
    global flip_horizontal, flip_vertical

    page.clean()
    page.title = "Webcam Railgun - Camera Flip Options"

    initial_choice = _get_current_choice()

    radio_group = ft.RadioGroup(
        content=ft.Column(
            controls=[
                ft.Radio(value="horizontal", label="Flip horizontally"),
                ft.Radio(value="vertical", label="Flip vertically"),
                ft.Radio(value="both", label="Flip both horizontally and vertically"),
                ft.Radio(value="none", label="No flip (default)"),
            ],
            spacing=10
        ),
        value=initial_choice
    )

    def on_submit(e):
        """Apply flip settings, persist to .ini, and navigate to camera feed."""
        global flip_horizontal, flip_vertical

        choice = radio_group.value

        if choice == "horizontal":
            flip_horizontal = True
            flip_vertical = False
        elif choice == "vertical":
            flip_horizontal = False
            flip_vertical = True
        elif choice == "both":
            flip_horizontal = True
            flip_vertical = True
        else:  # none
            flip_horizontal = False
            flip_vertical = False

        save_setting("Camera", "flip_horizontal", flip_horizontal)
        save_setting("Camera", "flip_vertical", flip_vertical)
        save_setting("Camera", "flip_choice", choice)

        from flet_app.screens.camera_feed import camera_feed_page
        camera_feed_page(page)

    def on_back(e):
        """Go back to camera selection."""
        from flet_app.screens.camera_selection import camera_selection_page
        camera_selection_page(page)

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
                                    on_click=on_back
                                ),
                                ft.Text("Camera Flip Options", size=30),
                            ]
                        ),
                        ft.Text("Please select flip option:", size=20),
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
