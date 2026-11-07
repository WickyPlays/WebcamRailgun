import flet as ft
from core.config import get_camera_config, save_setting
from flet_app.screens.cursor_offset import cursor_offset_page

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
    page.window.width = 800
    page.window.height = 600

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
        """Apply flip settings, persist to .ini, and navigate to button mapping."""
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

        cursor_offset_page(page)

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
                                    on_click=on_back,
                                    tooltip="Back to Camera Selection",
                                ),
                                ft.Text("Step 2: Camera Flip Options", size=26, weight=ft.FontWeight.BOLD),
                                ft.Container(width=40),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Text(
                            "Select flip options to match your camera orientation.",
                            size=14,
                            color=ft.Colors.GREY_400,
                        ),
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
