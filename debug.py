import cv2

DEBUG = False

def reject(reason, contour=None, approx=None):
    if DEBUG:
        print(f"[REJECT] {reason}")

        if contour is not None:
            print(
                f"        Area: {cv2.contourArea(contour):.1f}"
            )

        if approx is not None:
            print(
                f"        Corners: {len(approx)}"
            )

    return None

def print_contour_header(contour_index, area, area_ratio):
    if DEBUG:
        print()
        print(f"========== CONTOUR {contour_index} ==========")
        print(f"Area: {area:.1f}")
        print(f"Area ratio: {area_ratio:.4f}")


def print_perimeter_info(perimeter, approx_epsilon, detected_corners):
    if DEBUG:
        print(f"Perimeter: {perimeter:.1f}")
        print(f"Approx epsilon: {approx_epsilon}")
        print(f"Detected corners: {detected_corners}")

def print_ordered_points(points):
    if DEBUG:
        print(f"Ordered points:")
        print(f"  Top-left:     {points[0]}")
        print(f"  Top-right:    {points[1]}")
        print(f"  Bottom-right: {points[2]}")
        print(f"  Bottom-left:  {points[3]}")

def print_corner_value(corner_index, value):
    if DEBUG:
        print(
            f"Corner {corner_index} cosine: {value:.4f}"
        )


def print_dimensions(width_top, width_bottom, height_left, height_right, avg_width, avg_height, aspect_ratio):
    if DEBUG:
        print(f"Top width: {width_top:.1f}")
        print(f"Bottom width: {width_bottom:.1f}")
        print(f"Left height: {height_left:.1f}")
        print(f"Right height: {height_right:.1f}")
        print(f"Average width: {avg_width:.1f}")
        print(f"Average height: {avg_height:.1f}")
        print(f"Aspect ratio: {aspect_ratio:.3f}")

def print_border_info(white_pixel_count, total_border_pixels, white_ratio):
    if DEBUG:
        print(
            f"White pixels: "
            f"{white_pixel_count}/{total_border_pixels}"
        )

        print(
            f"White border ratio: "
            f"{white_ratio:.4f}"
        )


def print_valid_screen():
    if DEBUG:
        print("[VALID] EXACTLY 4-CORNER SCREEN FOUND")

def print_frame_header(width, height, contours_count, white_threshold, approx_epsilon):
    if DEBUG:
        print()
        print("========================================")
        print(
            f"FRAME: {width}x{height}"
        )
        print(
            f"Contours found: {contours_count}"
        )
        print(
            f"White threshold: {white_threshold}"
        )
        print(
            f"Approx epsilon: {approx_epsilon}"
        )

def print_selected_screen(area):
    if DEBUG:
        print()
        print(
            f"SELECTED SCREEN "
            f"AREA: {area:.1f}"
        )

def print_screen_center(screen_center):
    if DEBUG:
        print(
            f"Screen center: "
            f"{screen_center}"
        )
