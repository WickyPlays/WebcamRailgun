import asyncio
import threading
import cv2
import flet as ft
from core import (
    COLOR_TOLERANCE,
    CURSOR_ACTIVE,
    DEFAULT_FRAME_HEIGHT,
    DEFAULT_FRAME_WIDTH,
    open_camera,
    process_frame,
)
from flet_app.screens.camera_selection import selected_camera_index
from flet_app.screens.camera_flip_options import flip_horizontal, flip_vertical

FRAME_WIDTH = DEFAULT_FRAME_WIDTH
FRAME_HEIGHT = DEFAULT_FRAME_HEIGHT
DISPLAY_WIDTH = 560
DISPLAY_HEIGHT = 420

def camera_feed_page(page: ft.Page):
    """Camera feed screen with live processed screen detection and color mask side-by-side."""
    page.clean()
    page.title = "Webcam Railgun - Camera Feed"
    page.window.width = 1200
    page.window.height = 700

    stop_event = threading.Event()
    frame_lock = threading.Lock()
    latest_frames: tuple[int, int, bytes, bytes] | None = None
    latest_seq = 0

    color_tolerance = COLOR_TOLERANCE
    cursor_active = CURSOR_ACTIVE

    video_image = ft.RawImage(
        width=DISPLAY_WIDTH,
        height=DISPLAY_HEIGHT,
        fit=ft.BoxFit.CONTAIN,
        filter_quality=ft.FilterQuality.LOW,
    )

    mask_image = ft.RawImage(
        width=DISPLAY_WIDTH,
        height=DISPLAY_HEIGHT,
        fit=ft.BoxFit.CONTAIN,
        filter_quality=ft.FilterQuality.LOW,
    )

    def capture_loop():
        nonlocal latest_frames, latest_seq
        cap = open_camera(selected_camera_index, width=FRAME_WIDTH, height=FRAME_HEIGHT)
        try:
            while not stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    stop_event.wait(0.01)
                    continue

                h, w = frame.shape[:2]
                if w > FRAME_WIDTH or h > FRAME_HEIGHT:
                    frame = cv2.resize(
                        frame, (FRAME_WIDTH, FRAME_HEIGHT), interpolation=cv2.INTER_AREA
                    )
                    h, w = FRAME_HEIGHT, FRAME_WIDTH

                # Run screen detection & draw detection overlays from core (dissolved from index.py)
                processed_frame, color_mask, _, _ = process_frame(
                    frame,
                    color_tolerance=color_tolerance,
                    flip_horizontal=flip_horizontal,
                    flip_vertical=flip_vertical,
                    cursor_active=cursor_active,
                )

                # Convert BGR -> RGBA and Grayscale Mask -> RGBA in OpenCV C++ SIMD
                cam_rgba = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGBA)
                mask_rgba = cv2.cvtColor(color_mask, cv2.COLOR_GRAY2RGBA)

                cam_bytes = cam_rgba.tobytes()
                mask_bytes = mask_rgba.tobytes()

                with frame_lock:
                    latest_frames = (w, h, cam_bytes, mask_bytes)
                    latest_seq += 1
        finally:
            cap.release()

    async def render_loop():
        """Streams the latest camera and mask frames to Flutter GPU textures in parallel."""
        last_rendered_seq = -1
        while not stop_event.is_set():
            frame_data = None
            with frame_lock:
                if latest_frames is not None and latest_seq != last_rendered_seq:
                    frame_data = latest_frames
                    last_rendered_seq = latest_seq

            if frame_data is None:
                await asyncio.sleep(0.004)
                continue

            w, h, cam_pixels, mask_pixels = frame_data
            try:
                # Stream both textures concurrently with built-in frame-ack pacing
                await asyncio.gather(
                    video_image.render_rgba(w, h, cam_pixels, premultiplied=True),
                    mask_image.render_rgba(w, h, mask_pixels, premultiplied=True),
                )
            except Exception:
                break

    def on_keyboard(e: ft.KeyboardEvent):
        nonlocal color_tolerance
        key = e.key.upper()
        if key == "R":
            color_tolerance = max(0, color_tolerance - 5)
        elif key == "T":
            color_tolerance = min(255, color_tolerance + 5)

    def go_back(e):
        stop_event.set()
        page.on_keyboard_event = None
        from flet_app.screens.camera_flip_options import camera_flip_options_page
        camera_flip_options_page(page)

    page.on_keyboard_event = on_keyboard

    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.ADD, on_click=increment_click
    )

    page.add(
        ft.SafeArea(
            expand=True,
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row([
                            ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back),
                            ft.Text(
                                "Webcam Railgun",
                                size=20,
                            ),
                        ]),
                        ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text("Screen Detection", size=16),
                                        video_image,
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ft.Column(
                                    [
                                        ft.Text("Color Mask", size=16),
                                        mask_image,
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=16,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.Alignment.CENTER,
            ),
        )
    )

    def on_window_event(e: ft.WindowEvent):
        if e.type == ft.WindowEventType.CLOSE:
            stop_event.set()

    page.window.on_event = on_window_event
    page.on_disconnect = lambda _: stop_event.set()

    # Start camera capture thread and async GPU texture stream task
    threading.Thread(target=capture_loop, daemon=True).start()
    page.run_task(render_loop)
