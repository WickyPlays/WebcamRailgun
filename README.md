

Welcome to one of the wild project requested by no one ever!

## WebcamRailgun

WebcamRailgun is a computer vision project that transforms a toy gun with an attached webcam into a pointing device. The system uses classic OpenCV techniques to detect and track a target screen in the webcam feed, allowing the gun's pointing direction to be mapped to mouse cursor coordinates.

## Inspiration
This project was made on the fly as sort of imagination when I was walking through an arcade station and thinking about how cool it would be to control a computer with a gun without ever buying one of the dedicated arcade gun out there.

## How It Works

1. Using OpenCV to capture video feed from the webcam attached to any handheld items you have, preferably a gun toy.
2. It then converts frames to grayscale and applies thresholding to detect white regions (approx.)
3. Finds contours in the thresholded image, meaning to find possible outline area for it.
4. Filter contours based on:
   - Area (minimum and maximum thresholds)
   - Quadrilateral shape (4 corners)
   - Convexity
   - Corner angles (approximately 90 degrees)
5. **Center Calculation**: Computes the center point of the detected screen
6. **Cursor Mapping**: The detected center can be mapped to mouse cursor position (implementation pending)

## Installation

### Prerequisites

- Python 3.x
- Webcam attached to your gun toy
- A white screen or target for detection

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd WebcamRailgun
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Connect your webcam to the gun toy
2. Position a white screen or target in the camera's view
3. Run the script:
```bash
python index.py
```

4. The application will open two windows:
   - **Screen Detection**: Shows the video feed with detected screens highlighted in green
   - **White Mask**: Shows the thresholded binary image used for detection

5. Press `ESC` or `q` to exit the application

## Configuration

You can adjust the following parameters in `index.py`:

- `CAMERA_INDEX`: Webcam device index (default: 1)
- `MIN_AREA`: Minimum contour area for detection (default: 15000)
- `MAX_AREA_RATIO`: Maximum area as ratio of frame size (default: 0.95)
- `WHITE_THRESHOLD`: Threshold for white detection (default: 150)
- `APPROX_EPSILON`: Epsilon for polygon approximation (default: 0.02)

## Technical Details

### Detection Algorithm

The system uses a multi-stage detection pipeline:

1. **Grayscale Conversion**: Converts BGR frames to grayscale
2. **Thresholding**: Binary threshold to isolate white regions
3. **Morphological Operations**: 
   - Closing to fill gaps
   - Opening to remove noise
4. **Contour Detection**: Finds external contours using RETR_EXTERNAL
5. **Shape Filtering**: 
   - Area validation
   - Polygon approximation to 4 vertices
   - Convexity check
   - Corner angle validation (45-135 degrees)
6. **Center Calculation**: Computes mean of corner coordinates

### Visualization

- **Green rectangle**: Detected screen boundary
- **Blue circle**: Camera center point
- **Red circle**: Detected screen center point
- **"SCREEN" label**: Identifies the detected target

## Future Enhancements

- [ ] Mouse cursor integration for actual cursor control
- [ ] Calibration system for different screen sizes
- [ ] Multiple target support
- [ ] Improved lighting condition handling
- [ ] Gun orientation tracking using IMU
- [ ] Recoil simulation
- [ ] Configurable profiles for different games/applications

## Troubleshooting

### Webcam not detected
- Check if the correct `CAMERA_INDEX` is set (try 0 or 1)
- Ensure webcam drivers are installed
- Verify webcam is working with other applications

### Poor detection accuracy
- Adjust `WHITE_THRESHOLD` based on lighting conditions
- Modify `MIN_AREA` for different screen sizes
- Ensure the target screen is well-lit and contrasted

### Performance issues
- Reduce video resolution in camera settings
- Close other applications using the webcam
- Adjust morphological operation iterations

## License

This project is provided as-is for educational and experimental purposes.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
