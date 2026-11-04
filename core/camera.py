import cv2
import numpy as np
from pygrabber.dshow_graph import FilterGraph

DEFAULT_FRAME_WIDTH = 640
DEFAULT_FRAME_HEIGHT = 480
DEFAULT_FPS = 60

def list_cameras() -> list[str]:
    """Return the list of available DirectShow camera device names."""
    try:
        graph = FilterGraph()
        return list(graph.get_input_devices())
    except Exception:
        return []

def choose_camera() -> int:
    """List cameras on the console and prompt the user to select an index."""
    cameras = list_cameras()
    print("Available cameras:")

    for i, name in enumerate(cameras):
        print(f"Camera {i}: {name}")

    print(f"Total cameras: {len(cameras)}")

    camera_index = int(input("Enter camera index: "))
    return camera_index

def choose_camera_flip() -> tuple[bool, bool]:
    """Prompt the user on the console for horizontal/vertical camera flip options."""
    print("\nCamera flip options:")
    print("1. Flip horizontally")
    print("2. Flip vertically")
    print("3. Flip both horizontally and vertically")
    print("4. Skip (no flip)")
    flip_choice = input("Enter choice (1-4): ").strip()

    flip_horizontal = False
    flip_vertical = False

    if flip_choice == "1":
        flip_horizontal = True
        print("Camera will be flipped horizontally")
    elif flip_choice == "2":
        flip_vertical = True
        print("Camera will be flipped vertically")
    elif flip_choice == "3":
        flip_horizontal = True
        flip_vertical = True
        print("Camera will be flipped both horizontally and vertically")
    else:
        print("No flip applied")

    return flip_horizontal, flip_vertical

def open_camera(
    camera_index: int = 0,
    width: int = DEFAULT_FRAME_WIDTH,
    height: int = DEFAULT_FRAME_HEIGHT,
    fps: int = DEFAULT_FPS,
) -> cv2.VideoCapture:
    """Open a webcam using DirectShow on Windows for low latency and high FPS."""
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(camera_index)

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, fps)
    return cap

def apply_camera_flip(
    frame: np.ndarray,
    flip_horizontal: bool = False,
    flip_vertical: bool = False,
) -> np.ndarray:
    """Apply horizontal and/or vertical flipping to a frame."""
    if flip_horizontal and flip_vertical:
        return cv2.flip(frame, -1)
    if flip_horizontal:
        return cv2.flip(frame, 1)
    if flip_vertical:
        return cv2.flip(frame, 0)
    return frame
