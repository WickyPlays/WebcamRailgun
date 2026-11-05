from pathlib import Path
import flet as ft
from flet_app.screens.welcome import welcome_page

ASSETS_DIR = Path(__file__).resolve().parent / "flet_app" / "assets"

def main(page: ft.Page):
    page.title = "Webcam Railgun"
    page.window.width = 800
    page.window.height = 600

    welcome_page(page)

if __name__ == "__main__":
    ft.run(main, assets_dir=str(ASSETS_DIR))