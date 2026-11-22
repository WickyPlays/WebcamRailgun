import flet as ft

def show_info_modal(page: ft.Page):
    info_dialog = ft.AlertDialog(
        modal=False,
        title=ft.Row(
            [
                ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.AMBER_400, size=22),
                ft.Text("About Webcam Railgun", size=18, weight=ft.FontWeight.BOLD),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        content=ft.Container(
            width=460,
            content=ft.Column(
                [
                    ft.Text("What is it?", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400),
                    ft.Text(
                        "WebcamRailgun is a computer vision project that transforms a webcam into a mouse/keyboard pointing device. "
                        "It uses classic OpenCV techniques to detect and track a target screen in the webcam feed, mapping the pointer "
                        "direction to mouse cursor coordinates or keyboard inputs, with a Flet-based GUI for configuration and button mapping.",
                        size=13,
                        color=ft.Colors.GREY_300,
                    ),
                    ft.Divider(height=4, color=ft.Colors.WHITE_12),
                    ft.Text("Inspiration", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400),
                    ft.Text(
                        "The project is made on the fly as an idea while walking through an arcade station, thinking about how cool it would be "
                        "to control a computer with a gun without ever buying a dedicated arcade gun or cabinet.",
                        size=13,
                        color=ft.Colors.GREY_300,
                    ),
                    ft.Divider(height=4, color=ft.Colors.WHITE_12),
                    ft.Text("License", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400),
                    ft.Text(
                        "DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE (WTFPL)",
                        size=13,
                        color=ft.Colors.GREY_300,
                    ),
                    ft.Text(
                        "That's right. Just do whatever you want with this project, I don't care.",
                        size=13,
                        color=ft.Colors.GREY_300,
                    ),
                ],
                tight=True,
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
            ),
        ),
        actions=[
            ft.TextButton("Close", on_click=lambda _: page.pop_dialog()),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.show_dialog(info_dialog)
