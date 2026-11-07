import cv2
import numpy as np

from core.camera import apply_camera_flip
from core.geometry import angle_cos, compute_screen_center, order_points
from core.cursor import move_cursor_from_screen_position
from debug import (
    print_border_info,
    print_contour_header,
    print_corner_value,
    print_dimensions,
    print_frame_header,
    print_ordered_points,
    print_perimeter_info,
    print_screen_center,
    print_selected_screen,
    print_valid_screen,
    reject,
)

# Color to detect (BGR format)
"""
Can we even use or add feature to detect different colors?
It seemed that any other color than white was a bit bias due to lighting conditions.
"""
DETECT_COLOR = (255, 255, 255)  # White
CURSOR_ACTIVE = True

MIN_AREA_RATIO = 0.02
MAX_AREA_RATIO = 0.95
COLOR_TOLERANCE = 60  # Initial tolerance for color detection
APPROX_EPSILON = 0.02

_MORPH_KERNEL = np.ones((5, 5), np.uint8)

# This is the main function to check if screen is valid to start the detection
def is_screen_candidate(
    contour: np.ndarray,
    frame_shape: tuple[int, ...],
    gray: np.ndarray,
    color_mask: np.ndarray,
    contour_index: int,
    min_area_ratio: float = MIN_AREA_RATIO,
    max_area_ratio: float = MAX_AREA_RATIO,
    approx_epsilon: float = APPROX_EPSILON,
) -> np.ndarray | None:
    height, width = frame_shape[:2]
    frame_area = width * height

    area = cv2.contourArea(contour)
    area_ratio = area / frame_area

    print_contour_header(contour_index, area, area_ratio)

    # Region too small to detect further
    if area < frame_area * min_area_ratio:
        return reject(f"AREA TOO SMALL ({area_ratio:.4f} < {min_area_ratio})", contour)

    # Region too big to detect further
    if area > frame_area * max_area_ratio:
        return reject(f"AREA TOO LARGE ({area_ratio:.4f} > {max_area_ratio})", contour)

    # Calculate perimeter
    # This is more of a test if all 4 points of region can be chained together
    perimeter = cv2.arcLength(contour, True)
    if not perimeter:
        return reject("ZERO PERIMETER", contour)

    approx = cv2.approxPolyDP(contour, approx_epsilon * perimeter, True)

    print_perimeter_info(perimeter, approx_epsilon, len(approx))

    if len(approx) != 4:
        return reject(
            f"NOT EXACTLY 4 CORNERS (detected {len(approx)})", contour, approx
        )

    if not cv2.isContourConvex(approx):
        return reject("CONTOUR IS NOT CONVEX", contour, approx)

    points = approx.reshape(4, 2).astype(np.float32)
    points = order_points(points)

    print_ordered_points(points)

    corner_values = []

    for i in range(4):
        a = points[(i - 1) % 4]
        b = points[i]
        c = points[(i + 1) % 4]

        value = angle_cos(a, b, c)
        corner_values.append(value)

        print_corner_value(i + 1, value)

        if value > 0.35:
            return reject(
                f"CORNER {i + 1} TOO SHARP (cosine {value:.4f} > 0.35)", contour, approx
            )

    top_left, top_right, bottom_right, bottom_left = points

    width_top = np.linalg.norm(top_right - top_left)
    width_bottom = np.linalg.norm(bottom_right - bottom_left)

    height_left = np.linalg.norm(bottom_left - top_left)
    height_right = np.linalg.norm(bottom_right - top_right)

    avg_width = (width_top + width_bottom) / 2
    avg_height = (height_left + height_right) / 2

    aspect_ratio = avg_width / avg_height

    print_dimensions(
        width_top,
        width_bottom,
        height_left,
        height_right,
        avg_width,
        avg_height,
        aspect_ratio,
    )

    # Screen too small
    if avg_width < 100 or avg_height < 80:
        return reject(
            f"SCREEN TOO SMALL (width={avg_width:.1f}, height={avg_height:.1f})",
            contour,
            approx,
        )

    # Aspect ratio too small
    if aspect_ratio < 1.2:
        return reject(
            f"ASPECT RATIO TOO SMALL ({aspect_ratio:.3f} < 1.2)", contour, approx
        )

    # Aspect ratio too large
    if aspect_ratio > 5.0:
        return reject(
            f"ASPECT RATIO TOO LARGE ({aspect_ratio:.3f} > 5.0)", contour, approx
        )

    border_mask = np.zeros_like(gray)

    cv2.polylines(border_mask, [points.astype(np.int32)], True, 255, thickness=12)

    border_pixels = color_mask[border_mask > 0]

    if len(border_pixels) == 0:
        return reject("NO BORDER PIXELS", contour, approx)

    color_pixel_count = np.count_nonzero(border_pixels)
    color_ratio = color_pixel_count / len(border_pixels)

    print_border_info(color_pixel_count, len(border_pixels), color_ratio)

    if color_ratio < 0.30:
        return reject(
            f"COLOR BORDER RATIO TOO LOW ({color_ratio:.4f} < 0.30)", contour, approx
        )

    print_valid_screen()

    return points


def process_frame(
    frame: np.ndarray,
    *,
    detect_color: tuple[int, int, int] = DETECT_COLOR,
    color_tolerance: int = COLOR_TOLERANCE,
    approx_epsilon: float = APPROX_EPSILON,
    flip_horizontal: bool = False,
    flip_vertical: bool = False,
    cursor_active: bool = CURSOR_ACTIVE,
    cursor_offset_x: int = 0,
    cursor_offset_y: int = 0,
    draw_tolerance_overlay: bool = True,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None, tuple[int, int] | None]:
    """
    Run the screen detection pipeline on a BGR camera frame and draw visual overlays.
    """
    frame = apply_camera_flip(
        frame,
        flip_horizontal=flip_horizontal,
        flip_vertical=flip_vertical,
    )

    height, width = frame.shape[:2]

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Detect color border
    lower_color = np.array([max(0, detect_color[i] - color_tolerance) for i in range(3)])
    upper_color = np.array(
        [min(255, detect_color[i] + color_tolerance) for i in range(3)]
    )
    color_mask = cv2.inRange(frame, lower_color, upper_color)

    color_mask = cv2.morphologyEx(
        color_mask, cv2.MORPH_CLOSE, _MORPH_KERNEL, iterations=2
    )
    color_mask = cv2.morphologyEx(
        color_mask, cv2.MORPH_OPEN, _MORPH_KERNEL, iterations=1
    )

    contours, _ = cv2.findContours(
        color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    print_frame_header(width, height, len(contours), list(detect_color), approx_epsilon)

    candidates = []

    for contour_index, contour in enumerate(contours):
        points = is_screen_candidate(
            contour,
            frame.shape,
            gray,
            color_mask,
            contour_index,
            approx_epsilon=approx_epsilon,
        )

        if points is not None:
            area = cv2.contourArea(points)
            candidates.append((area, points))

    screen_points = None
    screen_center = None

    if candidates:
        candidates.sort(key=lambda item: item[0], reverse=True)
        screen_points = candidates[0][1]

        print_selected_screen(candidates[0][0])

    camera_center = (width // 2, height // 2)

    cv2.circle(frame, camera_center, 8, (0, 0, 255), -1, cv2.LINE_AA)

    if screen_points is not None:
        screen_int = screen_points.astype(np.int32)

        cv2.polylines(frame, [screen_int], True, (0, 255, 0), 4, cv2.LINE_AA)

        screen_center = compute_screen_center(screen_points)

        if 0 <= screen_center[0] < width and 0 <= screen_center[1] < height:
            cv2.circle(frame, screen_center, 10, detect_color, -1, cv2.LINE_AA)
            cv2.circle(frame, screen_center, 14, (255, 255, 255), 2, cv2.LINE_AA)
            print_screen_center(screen_center)

            # Move cursor based on camera position relative to detected screen
            if cursor_active:
                move_cursor_from_screen_position(
                    camera_center,
                    screen_points,
                    offset_x=cursor_offset_x,
                    offset_y=cursor_offset_y,
                )

    if draw_tolerance_overlay:
        cv2.putText(
            frame,
            f"Color Tolerance: {color_tolerance}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

    return frame, color_mask, screen_points, screen_center
