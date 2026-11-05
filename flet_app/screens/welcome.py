import flet as ft

def welcome_page(page: ft.Page):
    page.clean()
    page.title = "Webcam Railgun - Welcome"
    page.window.full_screen = False
    page.window.width = 800
    page.window.height = 600

    def on_start_test(e):
        from flet_app.screens.camera_selection import camera_selection_page
        camera_selection_page(page)

    def on_test_gun(e):
        from test.test_gun import gun_test_page

        def return_to_welcome():
            welcome_page(page)

        gun_test_page(page, on_exit=return_to_welcome)

    page.add(
        ft.SafeArea(
            expand=True,
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Image(
                            src="/gun_icon.png",
                            width=150,
                            height=150,
                            fit=ft.BoxFit.CONTAIN,
                        ),
                        ft.Text(
                            "Webcam Railgun",
                            size=40,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            "A mini project made by Wicky",
                            size=18,
                            color=ft.Colors.GREY_400,
                        ),
                        ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
                        ft.FilledButton(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.PLAY_ARROW, size=24),
                                    ft.Text("Start test", size=16, weight=ft.FontWeight.W_600),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=10,
                            ),
                            width=240,
                            height=50,
                            on_click=on_start_test,
                        ),
                        ft.OutlinedButton(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.SPORTS_ESPORTS, size=22),
                                    ft.Text("Test gun", size=16, weight=ft.FontWeight.W_600),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=10,
                            ),
                            width=240,
                            height=50,
                            on_click=on_test_gun,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                ),
                alignment=ft.Alignment.CENTER,
            ),
        )
    )
