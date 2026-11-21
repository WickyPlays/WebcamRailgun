from pathlib import Path
import flet as ft
from core.config import generate_default_ini
from flet_app.screens.welcome import welcome_page

ASSETS_DIR = Path(__file__).resolve().parent / "flet_app" / "assets"

def main(page: ft.Page):
    generate_default_ini()

    page.title = "Webcam Railgun"
    page.window.width = 960
    page.window.height = 700

    welcome_page(page)

if __name__ == "__main__":
    ft.run(main, assets_dir=str(ASSETS_DIR))