# Asked Devin to do this for me since I am too stupid about this kind of development...
# Contributions would be greatly appreciated!

import ctypes
from ctypes import wintypes
import threading
import time

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_longlong,
    wintypes.HWND,
    ctypes.c_uint,
    wintypes.WPARAM,
    wintypes.LPARAM,
)

class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("style", ctypes.c_uint),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HCURSOR),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", wintypes.HICON),
    ]

# Win32 Constants
CS_HREDRAW = 0x0002
CS_VREDRAW = 0x0001
WS_POPUP = 0x80000000
WS_VISIBLE = 0x10000000

WS_EX_TOPMOST = 0x00000008
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000

WHITE_BRUSH = 0
RGN_DIFF = 4
SW_SHOWNOACTIVATE = 4
SW_HIDE = 0
WM_CLOSE = 0x0010
WM_DESTROY = 0x0002
PM_REMOVE = 0x0001

HWND_TOPMOST = ctypes.c_void_p(-1)
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040

# Setup argtypes & restypes for 64-bit safety
user32.GetSystemMetrics.argtypes = [ctypes.c_int]
user32.GetSystemMetrics.restype = ctypes.c_int

gdi32.CreateRectRgn.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
gdi32.CreateRectRgn.restype = wintypes.HRGN

gdi32.CombineRgn.argtypes = [wintypes.HRGN, wintypes.HRGN, wintypes.HRGN, ctypes.c_int]
gdi32.CombineRgn.restype = ctypes.c_int

gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteObject.restype = wintypes.BOOL

gdi32.GetStockObject.argtypes = [ctypes.c_int]
gdi32.GetStockObject.restype = wintypes.HGDIOBJ

user32.SetWindowRgn.argtypes = [wintypes.HWND, wintypes.HRGN, wintypes.BOOL]
user32.SetWindowRgn.restype = ctypes.c_int

user32.CreateWindowExW.argtypes = [
    wintypes.DWORD,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.DWORD,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.HWND,
    wintypes.HMENU,
    wintypes.HINSTANCE,
    wintypes.LPVOID,
]
user32.CreateWindowExW.restype = wintypes.HWND

user32.SetWindowPos.argtypes = [
    wintypes.HWND,
    ctypes.c_void_p,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.UINT,
]
user32.SetWindowPos.restype = wintypes.BOOL

user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL

user32.UpdateWindow.argtypes = [wintypes.HWND]
user32.UpdateWindow.restype = wintypes.BOOL

user32.DestroyWindow.argtypes = [wintypes.HWND]
user32.DestroyWindow.restype = wintypes.BOOL

user32.IsWindow.argtypes = [wintypes.HWND]
user32.IsWindow.restype = wintypes.BOOL

user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostMessageW.restype = wintypes.BOOL

user32.DefWindowProcW.argtypes = [wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = ctypes.c_longlong

user32.RegisterClassExW.argtypes = [ctypes.POINTER(WNDCLASSEXW)]
user32.RegisterClassExW.restype = wintypes.ATOM

user32.UnregisterClassW.argtypes = [wintypes.LPCWSTR, wintypes.HINSTANCE]
user32.UnregisterClassW.restype = wintypes.BOOL

user32.PeekMessageW.argtypes = [
    ctypes.POINTER(wintypes.MSG),
    wintypes.HWND,
    wintypes.UINT,
    wintypes.UINT,
    wintypes.UINT,
]

user32.PeekMessageW.restype = wintypes.BOOL
user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.TranslateMessage.restype = wintypes.BOOL
user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.DispatchMessageW.restype = ctypes.c_longlong

def get_monitor_size() -> tuple[int, int]:
    """Return width and height of the primary monitor in pixels."""
    w = user32.GetSystemMetrics(0)  # SM_CXSCREEN
    h = user32.GetSystemMetrics(1)  # SM_CYSCREEN
    return int(w), int(h)

class WhiteBorderOverlay:
    """
    Creates a full-screen, click-through, topmost 20px white border overlay.
    Uses Win32 region clipping so the entire center is completely hollow and
    transparent with zero input or rendering overhead.
    """

    def __init__(self, thickness: int = 20):
        self.thickness = thickness
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._ready_event = threading.Event()
        self._hwnd: int | None = None
        self._wnd_proc_cb = WNDPROC(self._wnd_proc)

    def _wnd_proc(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        if msg == WM_CLOSE:
            user32.DestroyWindow(hwnd)
            return 0
        if msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def is_active(self) -> bool:
        return self._hwnd is not None and bool(user32.IsWindow(self._hwnd))

    def start(self, thickness: int | None = None):
        """Show the white border overlay."""
        if thickness is not None:
            self.thickness = thickness
        if self.is_active():
            return

        self._stop_event.clear()
        self._ready_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._ready_event.wait(timeout=2.0)

    def stop(self):
        """Hide and destroy the white border overlay."""
        self._stop_event.set()
        if self._hwnd and user32.IsWindow(self._hwnd):
            user32.PostMessageW(self._hwnd, WM_CLOSE, 0, 0)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._hwnd = None

    def toggle(self, thickness: int | None = None) -> bool:
        """Toggle the white border on/off. Returns True if now active, False if stopped."""
        if self.is_active():
            self.stop()
            return False
        else:
            self.start(thickness)
            return True

    def _run(self):
        hInstance = kernel32.GetModuleHandleW(None)
        class_name = f"WebcamRailgun_WhiteBorder_{id(self)}_{int(time.time() * 1000)}"

        wndclass = WNDCLASSEXW()
        wndclass.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wndclass.style = CS_HREDRAW | CS_VREDRAW
        wndclass.lpfnWndProc = self._wnd_proc_cb
        wndclass.cbClsExtra = 0
        wndclass.cbWndExtra = 0
        wndclass.hInstance = hInstance
        wndclass.hIcon = 0
        wndclass.hCursor = user32.LoadCursorW(0, 32512)  # IDC_ARROW
        wndclass.hbrBackground = gdi32.GetStockObject(WHITE_BRUSH)
        wndclass.lpszMenuName = None
        wndclass.lpszClassName = class_name
        wndclass.hIconSm = 0

        atom = user32.RegisterClassExW(ctypes.byref(wndclass))
        if not atom:
            self._ready_event.set()
            return

        width, height = get_monitor_size()

        # Styles:
        # WS_EX_TOPMOST: Stays above other full-screen or regular windows
        # WS_EX_TRANSPARENT: Mouse clicks pass straight through the border
        # WS_EX_TOOLWINDOW: Hidden from taskbar and Alt+Tab
        # WS_EX_NOACTIVATE: Does not steal focus from games
        ex_style = (
            WS_EX_TOPMOST
            | WS_EX_TRANSPARENT
            | WS_EX_TOOLWINDOW
            | WS_EX_NOACTIVATE
        )
        style = WS_POPUP | WS_VISIBLE

        hwnd = user32.CreateWindowExW(
            ex_style,
            class_name,
            "Webcam Railgun White Border",
            style,
            0,
            0,
            width,
            height,
            0,
            0,
            hInstance,
            None,
        )

        if not hwnd:
            user32.UnregisterClassW(class_name, hInstance)
            self._ready_event.set()
            return

        self._hwnd = hwnd

        # Hollow out the middle using region difference (RGN_DIFF)
        outer_rgn = gdi32.CreateRectRgn(0, 0, width, height)
        inner_rgn = gdi32.CreateRectRgn(
            self.thickness,
            self.thickness,
            max(self.thickness, width - self.thickness),
            max(self.thickness, height - self.thickness),
        )
        combined_rgn = gdi32.CreateRectRgn(0, 0, 0, 0)
        gdi32.CombineRgn(combined_rgn, outer_rgn, inner_rgn, RGN_DIFF)
        gdi32.DeleteObject(outer_rgn)
        gdi32.DeleteObject(inner_rgn)

        user32.SetWindowRgn(hwnd, combined_rgn, True)

        user32.SetWindowPos(
            hwnd,
            HWND_TOPMOST,
            0,
            0,
            width,
            height,
            SWP_NOACTIVATE | SWP_SHOWWINDOW,
        )
        user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)
        user32.UpdateWindow(hwnd)

        self._ready_event.set()

        msg = wintypes.MSG()
        while not self._stop_event.is_set():
            while user32.PeekMessageW(ctypes.byref(msg), 0, 0, 0, PM_REMOVE):
                if msg.message == WM_CLOSE:
                    user32.DestroyWindow(hwnd)
                    break
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            time.sleep(0.016)

        if user32.IsWindow(hwnd):
            user32.DestroyWindow(hwnd)

        user32.UnregisterClassW(class_name, hInstance)
        self._hwnd = None
