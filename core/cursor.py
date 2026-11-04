
import numpy as np
import cv2
import ctypes

user32 = ctypes.windll.user32

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000

ULONG_PTR = ctypes.c_size_t

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ULONG_PTR)
    ]

class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT)
    ]

class INPUT(ctypes.Structure):
    _anonymous_ = ("union",)
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("union", INPUT_UNION)
    ]

user32.SendInput.argtypes = [
    ctypes.c_uint,
    ctypes.POINTER(INPUT),
    ctypes.c_int
]
user32.SendInput.restype = ctypes.c_uint

def move_cursor_from_screen_position(camera_center, screen_points):
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)

    src = np.array(screen_points, dtype=np.float32)

    dst = np.array([
        [0, 0],
        [screen_width - 1, 0],
        [screen_width - 1, screen_height - 1],
        [0, screen_height - 1]
    ], dtype=np.float32)

    homography = cv2.getPerspectiveTransform(src, dst)

    camera_point = np.array(
        [[[camera_center[0], camera_center[1]]]],
        dtype=np.float32
    )

    screen_point = cv2.perspectiveTransform(
        camera_point, homography
    )[0][0]

    cursor_x = int(screen_point[0])
    cursor_y = int(screen_point[1])

    cursor_x = max(0, min(cursor_x, screen_width - 1))
    cursor_y = max(0, min(cursor_y, screen_height - 1))

    input_event = INPUT()
    input_event.type = 0
    input_event.mi = MOUSEINPUT(
        int(cursor_x * 65535 / (screen_width - 1)),
        int(cursor_y * 65535 / (screen_height - 1)),
        0,
        MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE,
        0,
        0
    )

    return user32.SendInput(
        1,
        ctypes.byref(input_event),
        ctypes.sizeof(INPUT)
    )