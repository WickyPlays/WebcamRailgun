# Python script provided by Wicky
#
# Please help to improve this script when necessary, as this is my best attempt at this so far
# There may be specific instances where this script will not work properly, 
# this is where you will come in to help
# Any supports are appreciated!

import cv2
import numpy as np

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

# Camera index (default is 0)
# In laptop case, default might be 1 if an external webcam is used
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError("Could not open webcam")

MIN_AREA_RATIO = 0.02
MAX_AREA_RATIO = 0.95
WHITE_THRESHOLD = 200
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
    white_mask,
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

    border_pixels = white_mask[border_mask > 0]

    if len(border_pixels) == 0:
        return reject("NO BORDER PIXELS", contour, approx)

    white_pixel_count = np.count_nonzero(border_pixels)
    white_ratio = white_pixel_count / len(border_pixels)

    print_border_info(white_pixel_count, len(border_pixels), white_ratio)

    if white_ratio < 0.30:
        return reject(f"WHITE BORDER RATIO TOO LOW ({white_ratio:.4f} < 0.30)", contour, approx)

    print_valid_screen()

    return points

# =========[MAIN AREA]===========
# This is where everything runs
# ===============================
while True:
    ret, frame = cap.read()

    if not ret:
        print("Could not read frame")
        break

    height, width = frame.shape[:2]

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    white_mask = cv2.inRange(blurred, WHITE_THRESHOLD, 255)

    kernel = np.ones((5, 5), np.uint8)

    white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel, iterations=1)

    contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    print_frame_header(width, height, len(contours), WHITE_THRESHOLD, APPROX_EPSILON)

    candidates = []

    for contour_index, contour in enumerate(contours):
        points = is_screen_candidate(contour, frame.shape, gray, white_mask, contour_index)

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
            cv2.circle(frame, screen_center, 10, (255, 0, 0), -1, cv2.LINE_AA)
            cv2.circle(frame, screen_center, 14, (255, 255, 255), 2, cv2.LINE_AA)
            print_screen_center(screen_center)

    # Show all needed windows to debug
    cv2.imshow("Camera", frame)
    # cv2.imshow("Gray", gray)
    cv2.imshow("White Mask", white_mask)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q") or key == 27:
        break

cap.release()
cv2.destroyAllWindows()