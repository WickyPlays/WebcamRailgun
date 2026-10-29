import numpy as np
import cv2
import ctypes

# Can't use pyautogui here due to the bottleneck
# This is the better approach for instant cursor movement
user32 = ctypes.windll.user32

def move_cursor_from_screen_position(camera_center, screen_points):

    # Get actual screen dimensions
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)

    # Define source points (detected screen corners in camera coordinates)
    src = np.array(screen_points, dtype=np.float32)

    # Define destination points (normalized 0-1 space for actual screen)
    dst = np.array([
        [0, 0],          # top-left
        [screen_width, 0],      # top-right
        [screen_width, screen_height],    # bottom-right
        [0, screen_height]           # bottom-left
    ], dtype=np.float32)

    # Calculate homography to map from camera space to screen space
    homography = cv2.getPerspectiveTransform(src, dst)

    # Transform camera center to screen coordinates
    camera_point = np.array([[camera_center[0]], [camera_center[1]], [1.0]], dtype=np.float32)
    screen_point = homography @ camera_point

    # Normalize homogeneous coordinates
    if screen_point[2, 0] != 0:
        screen_point /= screen_point[2, 0]

    # Get x, y coordinates
    cursor_x = int(screen_point[0, 0])
    cursor_y = int(screen_point[1, 0])

    # Clamp to screen bounds
    cursor_x = max(0, min(cursor_x, screen_width - 1))
    cursor_y = max(0, min(cursor_y, screen_height - 1))

    # Move cursor instantly using Windows API
    user32.SetCursorPos(cursor_x, cursor_y)

def set_sensitivity(scale_factor):
    global SCALE_FACTOR
    SCALE_FACTOR = scale_factor

def set_move_duration(duration):
    global MOVE_DURATION
    MOVE_DURATION = duration
