import cv2
import numpy as np

CAMERA_INDEX = 1
MIN_AREA = 15000
MAX_AREA_RATIO = 0.95
# considering 200 on this...
WHITE_THRESHOLD = 150
APPROX_EPSILON = 0.02

cap = cv2.VideoCapture(CAMERA_INDEX)

if not cap.isOpened():
    raise RuntimeError("Could not open webcam")

while True:
    ret, frame = cap.read()

    if not ret:
        break

    height, width = frame.shape[:2]

    camera_center = (width // 2, height // 2)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    _, white = cv2.threshold(
        gray,
        WHITE_THRESHOLD,
        255,
        cv2.THRESH_BINARY
    )

    kernel = np.ones((5, 5), np.uint8)

    white = cv2.morphologyEx(
        white,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=2
    )

    white = cv2.morphologyEx(
        white,
        cv2.MORPH_OPEN,
        kernel,
        iterations=1
    )

    contours, _ = cv2.findContours(
        white,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    detected = None
    largest_area = 0

    for contour in contours:
        area = cv2.contourArea(contour)

        if area < MIN_AREA:
            continue

        if area > width * height * MAX_AREA_RATIO:
            continue

        perimeter = cv2.arcLength(contour, True)

        approx = cv2.approxPolyDP(
            contour,
            APPROX_EPSILON * perimeter,
            True
        )

        if len(approx) != 4:
            continue

        if not cv2.isContourConvex(approx):
            continue

        points = approx.reshape(4, 2).astype(np.float32)

        center = np.mean(points, axis=0)

        angles = []

        for i in range(4):
            p1 = points[(i - 1) % 4] - center
            p2 = points[i] - center

            cosine = np.dot(p1, p2) / (
                np.linalg.norm(p1) * np.linalg.norm(p2)
            )

            angle = np.degrees(np.arccos(np.clip(cosine, -1, 1)))
            angles.append(angle)

        if any(angle < 45 or angle > 135 for angle in angles):
            continue

        if area > largest_area:
            largest_area = area
            detected = points

    if detected is not None:
        points = detected

        ordered = np.zeros((4, 2), dtype=np.float32)

        sums = points.sum(axis=1)
        differences = np.diff(points, axis=1).flatten()

        ordered[0] = points[np.argmin(sums)]
        ordered[1] = points[np.argmin(differences)]
        ordered[2] = points[np.argmax(sums)]
        ordered[3] = points[np.argmax(differences)]

        points_int = ordered.astype(np.int32)

        cv2.polylines(
            frame,
            [points_int],
            True,
            (0, 255, 0),
            3,
            cv2.LINE_AA
        )

        center = np.mean(ordered, axis=0)
        center = tuple(np.round(center).astype(int))

        cv2.circle(
            frame,
            center,
            8,
            (255, 0, 0),
            -1,
            cv2.LINE_AA
        )

        cv2.putText(
            frame,
            "SCREEN",
            (points_int[0][0], points_int[0][1] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
            cv2.LINE_AA
        )

    cv2.circle(
        frame,
        camera_center,
        8,
        (0, 0, 255),
        -1,
        cv2.LINE_AA
    )

    cv2.imshow("Screen Detection", frame)
    cv2.imshow("White Mask", white)

    key = cv2.waitKey(1) & 0xFF

    if key == 27 or key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()