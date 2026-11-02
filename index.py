# Python script provided by Wicky
#
# Please help to improve this script when necessary, as this is my best attempt at this so far
# There may be specific instances where this script will not work properly, 
# this is where you will come in to help
# Any supports are appreciated!

import cv2
import numpy as np
from pygrabber.dshow_graph import FilterGraph

# Color to detect (BGR format)
DETECT_COLOR = (255, 255, 255)  # White
CURSOR_ACTIVE = True

from debug import (
    reject,
    print_contour_header,
    print_perimeter_info,
    print_ordered_points,
    print_corner_value,
    print_dimensions,
    print_border_info,
    print_valid_screen,
    print_frame_header,
    print_selected_screen,
    print_screen_center
)
from cursor import move_cursor_from_screen_position

def choose_camera():
    graph = FilterGraph()
    cameras = graph.get_input_devices() 
    print("Available cameras:")
    
    for i, name in enumerate(cameras):
        print(f"Camera {i}: {name}")
    
    print(f"Total cameras: {len(cameras)}")
    
    camera_index = int(input("Enter camera index: "))
    return camera_index

def choose_camera_flip():
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

# List cam on console and let user choose first
camera_index = choose_camera()
cap = cv2.VideoCapture(camera_index)

if not cap.isOpened():
    raise RuntimeError("Could not open webcam")

# Ask for camera flip options
flip_horizontal, flip_vertical = choose_camera_flip()

MIN_AREA_RATIO = 0.02
MAX_AREA_RATIO = 0.95
COLOR_TOLERANCE = 60  # Initial tolerance for color detection (adjustable with R/T keys)
APPROX_EPSILON = 0.02

def order_points(points):
    points = np.array(points, dtype=np.float32)

    sum_vals = points.sum(axis=1)
    diff_vals = np.diff(points, axis=1).reshape(-1)

    top_left = points[np.argmin(sum_vals)]
    top_right = points[np.argmin(diff_vals)]
    bottom_right = points[np.argmax(sum_vals)]
    bottom_left = points[np.argmax(diff_vals)]

    return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)

def angle_cos(a, b, c):
    ba = a - b
    bc = c - b

    denominator = np.linalg.norm(ba) * np.linalg.norm(bc)

    if denominator == 0:
        return 1.0

    return abs(np.dot(ba, bc) / denominator)

# This is the main function to check if screen is valid to start the detection
def is_screen_candidate(
    contour,
    frame_shape,
    gray,
    color_mask,
    contour_index
) -> np.ndarray | None:
    height, width = frame_shape[:2]
    frame_area = width * height

    area = cv2.contourArea(contour)
    area_ratio = area / frame_area

    print_contour_header(contour_index, area, area_ratio)

    # Region too small to detect further
    if area < frame_area * MIN_AREA_RATIO:
        return reject(f"AREA TOO SMALL ({area_ratio:.4f} < {MIN_AREA_RATIO})", contour)

    # Region too big to detect further
    if area > frame_area * MAX_AREA_RATIO:
        return reject(f"AREA TOO LARGE ({area_ratio:.4f} > {MAX_AREA_RATIO})", contour)

    # Calculate perimeter
    # This is more of a test if all 4 points of region can be chained together
    perimeter = cv2.arcLength(contour, True)
    if not perimeter:
        return reject("ZERO PERIMETER", contour)

    approx = cv2.approxPolyDP(contour, APPROX_EPSILON * perimeter, True)

    print_perimeter_info(perimeter, APPROX_EPSILON, len(approx))

    if len(approx) != 4:
        return reject(f"NOT EXACTLY 4 CORNERS (detected {len(approx)})", contour, approx)

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
            return reject(f"CORNER {i + 1} TOO SHARP (cosine {value:.4f} > 0.35)", contour, approx)

    top_left, top_right, bottom_right, bottom_left = points

    width_top = np.linalg.norm(top_right - top_left)
    width_bottom = np.linalg.norm(bottom_right - bottom_left)

    height_left = np.linalg.norm(bottom_left - top_left)
    height_right = np.linalg.norm(bottom_right - top_right)

    avg_width = (width_top + width_bottom) / 2
    avg_height = (height_left + height_right) / 2

    aspect_ratio = avg_width / avg_height

    print_dimensions(width_top, width_bottom, height_left, height_right, avg_width, avg_height, aspect_ratio)

    # Screen too small
    if avg_width < 100 or avg_height < 80:
        return reject(f"SCREEN TOO SMALL (width={avg_width:.1f}, height={avg_height:.1f})", contour, approx)

    # Aspect ratio too small
    if aspect_ratio < 1.2:
        return reject(f"ASPECT RATIO TOO SMALL ({aspect_ratio:.3f} < 1.2)", contour, approx)

    # Aspect ratio too large
    if aspect_ratio > 5.0:
        return reject(f"ASPECT RATIO TOO LARGE ({aspect_ratio:.3f} > 5.0)", contour, approx)

    border_mask = np.zeros_like(gray)

    cv2.polylines(border_mask, [points.astype(np.int32)], True, 255, thickness=12)

    border_pixels = color_mask[border_mask > 0]

    if len(border_pixels) == 0:
        return reject("NO BORDER PIXELS", contour, approx)

    color_pixel_count = np.count_nonzero(border_pixels)
    color_ratio = color_pixel_count / len(border_pixels)

    print_border_info(color_pixel_count, len(border_pixels), color_ratio)

    if color_ratio < 0.30:
        return reject(f"COLOR BORDER RATIO TOO LOW ({color_ratio:.4f} < 0.30)", contour, approx)

    print_valid_screen()

    return points

# =========[MAIN AREA]===========
# This is where everything runs
# ===============================

# Create and resize windows
cv2.namedWindow("Camera", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Camera", 1280, 720)
cv2.namedWindow("Color Mask", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Color Mask", 640, 480)

while True:
    ret, frame = cap.read()

    if not ret:
        print("Could not read frame")
        break

    # Apply camera flip if selected
    if flip_horizontal:
        frame = cv2.flip(frame, 1)
    if flip_vertical:
        frame = cv2.flip(frame, 0)

    height, width = frame.shape[:2]

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Detect color border instead of white
    lower_color = np.array([max(0, DETECT_COLOR[i] - COLOR_TOLERANCE) for i in range(3)])
    upper_color = np.array([min(255, DETECT_COLOR[i] + COLOR_TOLERANCE) for i in range(3)])
    color_mask = cv2.inRange(frame, lower_color, upper_color)

    kernel = np.ones((5, 5), np.uint8)

    color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_OPEN, kernel, iterations=1)

    contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    print_frame_header(width, height, len(contours), list(DETECT_COLOR), APPROX_EPSILON)

    candidates = []

    for contour_index, contour in enumerate(contours):
        points = is_screen_candidate(contour, frame.shape, gray, color_mask, contour_index)

        if points is not None:
            area = cv2.contourArea(points)
            candidates.append((area, points))

    screen_points = None

    if candidates:
        candidates.sort(key=lambda item: item[0], reverse=True)
        screen_points = candidates[0][1]

        print_selected_screen(candidates[0][0])

    camera_center = (width // 2, height // 2)

    cv2.circle(frame, camera_center, 8, (0, 0, 255), -1, cv2.LINE_AA)

    if screen_points is not None:
        screen_int = screen_points.astype(np.int32)

        cv2.polylines(frame, [screen_int], True, (0, 255, 0), 4, cv2.LINE_AA)

        src = np.array([screen_points[0], screen_points[1], screen_points[2], screen_points[3]], dtype=np.float32)
        dst = np.array([[0, 0], [1000, 0], [1000, 600], [0, 600]], dtype=np.float32)

        homography = cv2.getPerspectiveTransform(src, dst)
        inverse_homography = np.linalg.inv(homography)
        projected_center = np.array([[500.0], [300.0], [1.0]], dtype=np.float32)
        screen_center_h = inverse_homography @ projected_center

        if screen_center_h[2, 0] != 0:
            screen_center_h /= screen_center_h[2, 0]

        screen_center = (int(round(screen_center_h[0, 0])), int(round(screen_center_h[1, 0])))

        if 0 <= screen_center[0] < width and 0 <= screen_center[1] < height:
            cv2.circle(frame, screen_center, 10, DETECT_COLOR, -1, cv2.LINE_AA)
            cv2.circle(frame, screen_center, 14, (255, 255, 255), 2, cv2.LINE_AA)
            print_screen_center(screen_center)

            # Move cursor based on camera position relative to detected screen
            if CURSOR_ACTIVE:
                move_cursor_from_screen_position(camera_center, screen_points)

    # Display current color tolerance on camera view
    cv2.putText(frame, f"Color Tolerance: {COLOR_TOLERANCE} (R/T to adjust)", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # Show all needed windows to debug
    cv2.imshow("Camera", frame)
    cv2.imshow("Color Mask", color_mask)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q") or key == 27:
        break
    elif key == ord("r") or key == ord("R"):
        COLOR_TOLERANCE = max(0, COLOR_TOLERANCE - 5)
        print(f"Color tolerance decreased to {COLOR_TOLERANCE}")
    elif key == ord("t") or key == ord("T"):
        COLOR_TOLERANCE = min(255, COLOR_TOLERANCE + 5)
        print(f"Color tolerance increased to {COLOR_TOLERANCE}")

cap.release()
cv2.destroyAllWindows()