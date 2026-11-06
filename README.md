

# WebcamRailgun

Welcome to one of the wild project requested by no one ever!

This mini project is designed specifically for Youtube video, but you can use this as reference

## What is it?
WebcamRailgun is a computer vision project that transforms a webcam into a mouse pointing device. The system uses classic OpenCV techniques to detect and track a target screen in the webcam feed, allowing the pointer direction to be mapped to mouse cursor coordinates.

## Inspiration
This project was made on the fly as sort of idea when I was walking through an arcade station and thinking about how cool it would be to control a computer with a gun without ever buying one of the dedicated arcade gun or even a cabinet out there.

## How does it work?

1. Using OpenCV to capture video feed from the webcam attached to any handheld items you have, preferably a gun toy.
2. It then converts frames to grayscale and applies thresholding to detect white regions (approx.)
3. Finds contours in the thresholded image, meaning to find possible outline area for it.
4. Filter contours based on:
   - Area (minimum and maximum thresholds)
   - Quadrilateral shape (4 corners)
   - Convexity
   - Corner angles (approximately 90 degrees)
5. From all of the above, compute the center point of the detected screen
6. The computed center can be mapped to mouse cursor position (implementation pending)

## Installation

### Prerequisites

- Python 3.x (This project is tested on Python 3.15.2)
- Webcam attached to anything that points (aka your gun toy)
- A white border on your screen

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd WebcamRailgun
```

2. Create a virtual environment (if necessary):
```bash
python -m venv .venv
```
Then, in your Linux terminal:
```bash
source .venv/bin/activate
```
Or in your Windows terminal:
```bash
.venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Mount your webcam to any physical pointing items you have.
2. Position a white screen or target in the camera's view
3. Run the script:
```bash
python index.py
```

4. The application will open two windows:
   - **Camera**: Shows the video feed with detected screens highlighted in green
   - **White Mask**: Shows the thresholded binary image used for detection

5. Press `ESC` or `q` to exit the application

## Debug Mode
- Set `DEBUG = True` in `debug.py` to enable verbose logging
- Set `DEBUG = False` in `debug.py` to disable debug output

## Technical Details

### Detection Algorithm

The system uses a multi-stage detection pipeline:

1. **Grayscale Conversion**: Converts BGR frames to grayscale
2. **Gaussian Blur**: Applies 5x5 blur to reduce noise
3. **Thresholding**: Binary threshold to isolate white regions (default: 200)
4. **Morphological Operations**:
   - Closing (2 iterations) to fill gaps
   - Opening (1 iteration) to remove noise
5. **Contour Detection**: Finds external contours using RETR_EXTERNAL
6. **Shape Filtering**:
   - Area validation (2% to 95% of frame area)
   - Polygon approximation to 4 vertices (epsilon: 0.02)
   - Convexity check
   - Corner angle validation (cosine < 0.35, approximately 70+ degrees)
   - Dimension validation (minimum width: 100, minimum height: 80)
   - Aspect ratio validation (1.2 to 5.0)
   - White border ratio validation (minimum 30% white pixels)
7. **Center Calculation**: Uses homography transformation to compute screen center

## Troubleshooting

### Webcam not detected
- Check if the correct camera index is set (try 0 or 1)
- Ensure webcam drivers are installed
- Verify webcam is working with other applications

### Performance issues
- Reduce video resolution in camera settings
- Close other applications using the webcam
- Adjust morphological operation iterations

## Notice to AI usage

This project is made with the assist of Devin AI, but only to help with cases in the homography transformation math that I have been stuck on for ages. I still did all the coding and testing myself.
AI usage is allowed on contributions, but always to triple check before actually pushing the code!

## License

This project is licensed under [WTFPL](LICENSE) (Just do whatever you want with it, I don't care).

## Contributing

Contributions are always welcome for this little script! Feel free to submit issues or pull requests.
