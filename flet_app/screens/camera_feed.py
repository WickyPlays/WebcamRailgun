import asyncio
import threading
import cv2
import flet as ft
from core import (
    COLOR_TOLERANCE,
    CURSOR_ACTIVE,
    DEFAULT_FRAME_HEIGHT,
    DEFAULT_FRAME_WIDTH,
    GunController,
    get_camera_config,
    get_detection_config,
    get_gun_config,
    get_view_config,
    open_camera,
    process_frame,
    save_setting,
)

FRAME_WIDTH = DEFAULT_FRAME_WIDTH
FRAME_HEIGHT = DEFAULT_FRAME_HEIGHT
DISPLAY_WIDTH = 560
DISPLAY_HEIGHT = 420

def camera_feed_page(page: ft.Page):
    """Camera feed screen with live processed screen detection and color mask side-by-side."""
    page.clean()
    page.title = "Webcam Railgun - Camera Feed"
    page.window.width = 1200
    page.window.height = 720

    stop_event = threading.Event()
    frame_lock = threading.Lock()
    latest_frames: tuple[int, int, bytes, bytes] | None = None
    latest_seq = 0
    is_screen_targeted = False

    # Load persisted settings from config
    cam_cfg = get_camera_config()
    selected_camera_index = cam_cfg.get("selected_camera_index", 0)
    flip_horizontal = cam_cfg.get("flip_horizontal", False)
    flip_vertical = cam_cfg.get("flip_vertical", False)

    det_cfg = get_detection_config()
    view_cfg = get_view_config()
    gun_cfg = get_gun_config()

    color_tolerance = det_cfg.get("color_tolerance", COLOR_TOLERANCE)
    cursor_active = CURSOR_ACTIVE

    cam_visible = view_cfg.get("cam_visible", True)
    mask_visible = view_cfg.get("mask_visible", True)
    views_flipped = view_cfg.get("views_flipped", False)

    # Initialize ESP32 serial gun controller if enabled
    gun_controller: GunController | None = None
    if gun_cfg.get("enabled", True):
        gun_controller = GunController(
            port=gun_cfg.get("port", "AUTO"),
            baudrate=gun_cfg.get("baudrate", 115200),
            is_screen_targeted=lambda: is_screen_targeted,
            offscreen_reload=gun_cfg.get("offscreen_reload", False),
        )
        gun_controller.start()

    video_image = ft.RawImage(
        width=DISPLAY_WIDTH,
        height=DISPLAY_HEIGHT,
        fit=ft.BoxFit.CONTAIN,
        filter_quality=ft.FilterQuality.LOW,
        visible=cam_visible,
    )

    mask_image = ft.RawImage(
        width=DISPLAY_WIDTH,
        height=DISPLAY_HEIGHT,
        fit=ft.BoxFit.CONTAIN,
        filter_quality=ft.FilterQuality.LOW,
        visible=mask_visible,
    )

    cam_placeholder = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.VISIBILITY_OFF, size=48, color=ft.Colors.GREY_500),
                ft.Text("Screen Detection hidden", size=14, color=ft.Colors.GREY_500),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=DISPLAY_WIDTH,
        height=DISPLAY_HEIGHT,
        bgcolor=ft.Colors.BLACK_12,
        border_radius=8,
        visible=not cam_visible,
    )

    mask_placeholder = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.VISIBILITY_OFF, size=48, color=ft.Colors.GREY_500),
                ft.Text("Color Mask hidden", size=14, color=ft.Colors.GREY_500),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=DISPLAY_WIDTH,
        height=DISPLAY_HEIGHT,
        bgcolor=ft.Colors.BLACK_12,
        border_radius=8,
        visible=not mask_visible,
    )

    def capture_loop():
        nonlocal latest_frames, latest_seq, is_screen_targeted
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
                processed_frame, color_mask, screen_points, _ = process_frame(
                    frame,
                    color_tolerance=color_tolerance,
                    flip_horizontal=flip_horizontal,
                    flip_vertical=flip_vertical,
                    cursor_active=cursor_active,
                )
                is_screen_targeted = screen_points is not None

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
            if not cam_visible and not mask_visible:
                await asyncio.sleep(0.02)
                continue

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
                if cam_visible and mask_visible:
                    await asyncio.gather(
                        video_image.render_rgba(w, h, cam_pixels, premultiplied=True),
                        mask_image.render_rgba(w, h, mask_pixels, premultiplied=True),
                    )
                elif cam_visible:
                    await video_image.render_rgba(w, h, cam_pixels, premultiplied=True)
                elif mask_visible:
                    await mask_image.render_rgba(w, h, mask_pixels, premultiplied=True)
            except Exception:
                break

    def cleanup():
        stop_event.set()
        if gun_controller:
            gun_controller.stop()

    def go_back(e):
        cleanup()
        from flet_app.screens.button_mapping import button_mapping_page
        button_mapping_page(page)

    page.floating_action_button = None

    def toggle_cam_visibility(e):
        nonlocal cam_visible
        cam_visible = not cam_visible
        video_image.visible = cam_visible
        cam_placeholder.visible = not cam_visible
        cam_visibility_button.icon = (
            ft.Icons.VISIBILITY if cam_visible else ft.Icons.VISIBILITY_OFF
        )
        cam_visibility_button.tooltip = "Hide view" if cam_visible else "Show view"
        save_setting("View", "cam_visible", cam_visible)
        cam_column.update()

    def toggle_mask_visibility(e):
        nonlocal mask_visible
        mask_visible = not mask_visible
        mask_image.visible = mask_visible
        mask_placeholder.visible = not mask_visible
        mask_visibility_button.icon = (
            ft.Icons.VISIBILITY if mask_visible else ft.Icons.VISIBILITY_OFF
        )
        mask_visibility_button.tooltip = "Hide view" if mask_visible else "Show view"
        save_setting("View", "mask_visible", mask_visible)
        mask_column.update()

    async def refresh_cam_view(e):
        nonlocal cam_visible
        if not cam_visible:
            cam_visible = True
            video_image.visible = True
            cam_placeholder.visible = False
            cam_visibility_button.icon = ft.Icons.VISIBILITY
            cam_visibility_button.tooltip = "Hide view"
            save_setting("View", "cam_visible", cam_visible)
            cam_column.update()

        frame_data = None
        with frame_lock:
            if latest_frames is not None:
                frame_data = latest_frames

        if frame_data is not None:
            w, h, cam_pixels, _ = frame_data
            try:
                await video_image.render_rgba(w, h, cam_pixels, premultiplied=True)
            except Exception:
                pass
        video_image.update()

    async def refresh_mask_view(e):
        nonlocal mask_visible
        if not mask_visible:
            mask_visible = True
            mask_image.visible = True
            mask_placeholder.visible = False
            mask_visibility_button.icon = ft.Icons.VISIBILITY
            mask_visibility_button.tooltip = "Hide view"
            save_setting("View", "mask_visible", mask_visible)
            mask_column.update()

        frame_data = None
        with frame_lock:
            if latest_frames is not None:
                frame_data = latest_frames

        if frame_data is not None:
            w, h, _, mask_pixels = frame_data
            try:
                await mask_image.render_rgba(w, h, mask_pixels, premultiplied=True)
            except Exception:
                pass
        mask_image.update()

    cam_visibility_button = ft.IconButton(
        icon=ft.Icons.VISIBILITY if cam_visible else ft.Icons.VISIBILITY_OFF,
        tooltip="Hide view" if cam_visible else "Show view",
        on_click=toggle_cam_visibility,
    )

    cam_refresh_button = ft.IconButton(
        icon=ft.Icons.REFRESH,
        tooltip="Refresh view",
        on_click=refresh_cam_view,
    )

    mask_visibility_button = ft.IconButton(
        icon=ft.Icons.VISIBILITY if mask_visible else ft.Icons.VISIBILITY_OFF,
        tooltip="Hide view" if mask_visible else "Show view",
        on_click=toggle_mask_visibility,
    )

    mask_refresh_button = ft.IconButton(
        icon=ft.Icons.REFRESH,
        tooltip="Refresh view",
        on_click=refresh_mask_view,
    )

    cam_column = ft.Column(
        [
            ft.Row(
                [
                    ft.Text("Screen Detection", size=16),
                    cam_visibility_button,
                    cam_refresh_button,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            video_image,
            cam_placeholder,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    mask_column = ft.Column(
        [
            ft.Row(
                [
                    ft.Text("Color Mask", size=16),
                    mask_visibility_button,
                    mask_refresh_button,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            mask_image,
            mask_placeholder,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    views_row = ft.Row(
        [mask_column, cam_column] if views_flipped else [cam_column, mask_column],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=16,
    )

    def toggle_flip_view(e):
        nonlocal views_flipped
        views_flipped = not views_flipped
        views_row.controls = (
            [mask_column, cam_column] if views_flipped else [cam_column, mask_column]
        )
        save_setting("View", "views_flipped", views_flipped)
        views_row.update()

    tolerance_text = ft.Text(str(color_tolerance), size=16, weight=ft.FontWeight.BOLD)

    def decrease_tolerance(e):
        nonlocal color_tolerance
        color_tolerance = max(0, color_tolerance - 5)
        tolerance_text.value = str(color_tolerance)
        save_setting("Detection", "color_tolerance", color_tolerance)
        tolerance_text.update()

    def increase_tolerance(e):
        nonlocal color_tolerance
        color_tolerance = min(255, color_tolerance + 5)
        tolerance_text.value = str(color_tolerance)
        save_setting("Detection", "color_tolerance", color_tolerance)
        tolerance_text.update()

    tolerance_row = ft.Row(
        [
            ft.Text("Tolerance:", size=16),
            ft.IconButton(
                icon=ft.Icons.REMOVE,
                tooltip="Decrease tolerance",
                on_click=decrease_tolerance,
            ),
            tolerance_text,
            ft.IconButton(
                icon=ft.Icons.ADD,
                tooltip="Increase tolerance",
                on_click=increase_tolerance,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    page.add(
        ft.SafeArea(
            expand=True,
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Row(
                                    [
                                        ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back),
                                        ft.Text(
                                            "Webcam Railgun",
                                            size=20,
                                        ),
                                    ],
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.SWAP_HORIZ,
                                    tooltip="Flip view between mask and cam",
                                    on_click=toggle_flip_view,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        views_row,
                        tolerance_row,
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
            cleanup()

    page.window.on_event = on_window_event
    page.on_disconnect = lambda _: cleanup()

    # Start camera capture thread and async GPU texture stream task
    threading.Thread(target=capture_loop, daemon=True).start()
    page.run_task(render_loop)
