import flet as ft
from flet_app.screens.camera_selection import camera_selection_page

def main(page: ft.Page):
    page.title = "Webcam Railgun"
    page.window.width = 800
    page.window.height = 600

    camera_selection_page(page)

if __name__ == "__main__":
    ft.run(main)