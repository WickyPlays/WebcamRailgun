import cv2
import numpy as np

def order_points(points: np.ndarray) -> np.ndarray:
    """Order 4 quadrilateral points as [top-left, top-right, bottom-right, bottom-left]."""
    points = np.array(points, dtype=np.float32)

    sum_vals = points.sum(axis=1)
    diff_vals = np.diff(points, axis=1).reshape(-1)

    top_left = points[np.argmin(sum_vals)]
    top_right = points[np.argmin(diff_vals)]
    bottom_right = points[np.argmax(sum_vals)]
    bottom_left = points[np.argmax(diff_vals)]

    return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)

def angle_cos(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Return the absolute cosine of the angle at vertex b formed by segments ba and bc."""
    ba = a - b
    bc = c - b

    denominator = np.linalg.norm(ba) * np.linalg.norm(bc)

    if denominator == 0:
        return 1.0

    return float(abs(np.dot(ba, bc) / denominator))

def compute_screen_center(screen_points: np.ndarray) -> tuple[int, int]:
    """Project the center of the normalized screen plane back into camera pixel coordinates."""
    src = np.array(
        [screen_points[0], screen_points[1], screen_points[2], screen_points[3]],
        dtype=np.float32,
    )
    dst = np.array([[0, 0], [1000, 0], [1000, 600], [0, 600]], dtype=np.float32)

    homography = cv2.getPerspectiveTransform(src, dst)
    inverse_homography = np.linalg.inv(homography)
    projected_center = np.array([[500.0], [300.0], [1.0]], dtype=np.float32)
    screen_center_h = inverse_homography @ projected_center

    if screen_center_h[2, 0] != 0:
        screen_center_h /= screen_center_h[2, 0]

    return (
        int(round(float(screen_center_h[0, 0]))),
        int(round(float(screen_center_h[1, 0]))),
    )
