import flet as ft

# Global variables to store flip options
flip_horizontal = False
flip_vertical = False


def camera_flip_options_page(page: ft.Page):
    """Camera flip options screen."""
    global flip_horizontal, flip_vertical

    page.clean()
    page.title = "Webcam Railgun - Camera Flip Options"

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
        value="none"
    )

    def on_submit(e):
        """Apply flip settings and navigate to camera feed."""
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
