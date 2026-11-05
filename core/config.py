import configparser
from pathlib import Path
from typing import Any

# Default path for the configuration INI file in the project root
CONFIG_FILE_PATH = Path(__file__).resolve().parent.parent / "config.ini"

# Default configuration template
DEFAULT_CONFIG: dict[str, dict[str, str]] = {
    "Camera": {
        "selected_camera_index": "0",
        "flip_horizontal": "False",
        "flip_vertical": "False",
        "flip_choice": "none",
    },
    "Detection": {
        "color_tolerance": "60",
    },
    "View": {
        "cam_visible": "True",
        "mask_visible": "True",
        "views_flipped": "False",
    },
    "Gun": {
        "port": "AUTO",
        "baudrate": "115200",
        "enabled": "True",
        "offscreen_reload": "True",
    },
    "Buttons": {
        "trigger": "Left Click",
        "secondary": "Right Click",
        "btnex1": "R",
        "btnex2": "Shift",
        "btnex3": "Escape",
    },
}

def generate_default_ini(file_path: Path | str = CONFIG_FILE_PATH, force: bool = False) -> Path:
    path = Path(file_path)
    if path.exists() and not force:
        return path

    config = configparser.ConfigParser()
    for section, options in DEFAULT_CONFIG.items():
        config[section] = options

    with open(path, "w", encoding="utf-8") as f:
        config.write(f)

    return path

def load_config(file_path: Path | str = CONFIG_FILE_PATH) -> configparser.ConfigParser:
    path = Path(file_path)
    if not path.exists():
        generate_default_ini(path)

    config = configparser.ConfigParser()
    config.read(path, encoding="utf-8")

    # Ensure all expected sections and keys exist with fallback defaults
    changed = False
    for section, options in DEFAULT_CONFIG.items():
        if not config.has_section(section):
            config.add_section(section)
            changed = True
        for key, val in options.items():
            if not config.has_option(section, key):
                config.set(section, key, val)
                changed = True

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            config.write(f)

    return config

def save_setting(
    section: str,
    key: str,
    value: Any,
    file_path: Path | str = CONFIG_FILE_PATH,
) -> None:
    config = load_config(file_path)
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, key, str(value))

    path = Path(file_path)
    with open(path, "w", encoding="utf-8") as f:
        config.write(f)

def get_camera_config(file_path: Path | str = CONFIG_FILE_PATH) -> dict[str, Any]:
    config = load_config(file_path)
    return {
        "selected_camera_index": config.getint("Camera", "selected_camera_index", fallback=0),
        "flip_horizontal": config.getboolean("Camera", "flip_horizontal", fallback=False),
        "flip_vertical": config.getboolean("Camera", "flip_vertical", fallback=False),
        "flip_choice": config.get("Camera", "flip_choice", fallback="none"),
    }

def get_detection_config(file_path: Path | str = CONFIG_FILE_PATH) -> dict[str, Any]:
    config = load_config(file_path)
    return {
        "color_tolerance": config.getint("Detection", "color_tolerance", fallback=60),
    }

def get_view_config(file_path: Path | str = CONFIG_FILE_PATH) -> dict[str, Any]:
    config = load_config(file_path)
    return {
        "cam_visible": config.getboolean("View", "cam_visible", fallback=True),
        "mask_visible": config.getboolean("View", "mask_visible", fallback=True),
        "views_flipped": config.getboolean("View", "views_flipped", fallback=False),
    }

def get_gun_config(file_path: Path | str = CONFIG_FILE_PATH) -> dict[str, Any]:
    config = load_config(file_path)
    return {
        "port": config.get("Gun", "port", fallback="AUTO"),
        "baudrate": config.getint("Gun", "baudrate", fallback=115200),
        "enabled": config.getboolean("Gun", "enabled", fallback=True),
        "offscreen_reload": config.getboolean("Gun", "offscreen_reload", fallback=True),
    }

def get_buttons_config(file_path: Path | str = CONFIG_FILE_PATH) -> dict[str, str]:
    config = load_config(file_path)
    return {
        "trigger": config.get("Buttons", "trigger", fallback="Left Click"),
        "secondary": config.get("Buttons", "secondary", fallback="Right Click"),
        "btnex1": config.get("Buttons", "btnex1", fallback="R"),
        "btnex2": config.get("Buttons", "btnex2", fallback="Shift"),
        "btnex3": config.get("Buttons", "btnex3", fallback="Escape"),
    }

if __name__ == "__main__":
    generated_path = generate_default_ini(force=True)
    print(f"Generated default config at: {generated_path.resolve()}")
