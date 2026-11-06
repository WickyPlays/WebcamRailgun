# WebcamRailgun

Welcome to one of the wild projects requested by no one ever!

This mini project is designed specifically for a YouTube video, but you can use this as a reference.

## What is it?
WebcamRailgun is a computer vision project that transforms a webcam into a mouse/keyboard pointing device. The system uses classic OpenCV techniques to detect and track a target screen in the webcam feed, allowing the pointer direction to be mapped to mouse cursor coordinates or keyboard inputs; using a Flet-based GUI for easy configuration and button mapping.

## Inspiration
This project was made on the fly as an idea when I was walking through an arcade station and thinking about how cool it would be to control a computer with a gun without ever buying one of the dedicated arcade gun or even a cabinet out there.

## How does it work?

1. Using OpenCV to capture video feed from the webcam attached to any handheld items you have, preferably a gun toy.
2. It then converts frames to grayscale and applies thresholding to detect white regions.
3. Finds contours in the thresholded image to find possible outline areas.
4. Filter contours based on:
   - Area (minimum and maximum thresholds)
   - Quadrilateral shape (4 corners)
   - Convexity
   - Corner angles (approximately 90 degrees)
5. From all of the above, compute the center point of the detected screen
6. The computed center is mapped to mouse cursor position or keyboard inputs
7. ESP32 gun controller sends button events over serial to trigger mapped actions

## Installation

### Prerequisites

- Python 3.x (This project is tested on Python 3.15)
- Webcam attached to anything that points (aka your gun toy)
- A white border on your screen
- ESP32 microcontroller (optional, for hardware gun controller)
- USB-to-Serial adapter (for ESP32 connection)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd WebcamRailgun
```

2. Create a virtual environment:
```bash
python -m venv .venv
```
On Linux:
```bash
source .venv/bin/activate
```
On Windows:
```bash
.venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### ESP32 Setup (Optional)

If using the hardware gun controller:

1. Open `arduino_gun_esp32/arduino_gun_esp32.ino` in Arduino IDE
2. Install ESP32 board support in Arduino IDE
3. Upload the firmware to your ESP32
4. Connect the ESP32 to your computer via USB

## Usage

### Starting the Application

Run the Flet application:
```bash
python main.py
```

Or using Flet CLI:
```bash
flet run main.py
```

### Configuration Flow

The application guides you through setup in several steps:

1. **Camera Selection**
   - Select your webcam from the list
   - Click "Continue" to proceed

2. **Camera Flip Options**
   - Choose camera orientation (horizontal/vertical flip)
   - Click "Continue" to proceed

3. **Button Mapping** (Optional)
   - Map your gun buttons to mouse/keyboard actions
   - Available buttons:
     - **Trigger**: Main fire button (default: Left Click)
     - **Secondary**: Secondary button (default: Right Click)
     - **Custom Button A**: Configurable (default: R key)
     - **Custom Button B**: Configurable (default: Shift)
     - **Custom Button C**: Configurable (default: Escape)
   - Click the keyboard icon to remap by pressing a key
   - Use the dropdown to select predefined actions
   - Click "Continue" to proceed

4. **Camera Feed**
   - View live camera feed with screen detection
   - Toggle between camera view and color mask view using the button in the header
   - Settings are automatically saved to `config.ini`

### Configuration File

All settings are stored in `config.ini`:

```ini
[Camera]
selected_camera_index = 0
flip_horizontal = False
flip_vertical = False
flip_choice = none

[Detection]
color_tolerance = 60

[View]
cam_visible = True
mask_visible = True
views_flipped = False

[Gun]
port = AUTO
baudrate = 115200
enabled = True
offscreen_reload = False

[Buttons]
trigger = Left Click
secondary = Right Click
btnexA = R
btnexB = Shift
btnexC = Escape
```

### Button Mappings

Available actions for button mapping:

**Mouse Actions:**
- Left Click
- Right Click
- Middle Click

**Keyboard Actions:**
- Space, Enter, Escape, Shift, Ctrl, Alt, Tab, Backspace
- Letters A-Z
- Numbers 0-9
- Arrow keys (Up, Down, Left, Right)
- Function keys (F1-F12)

### Offscreen Reload Feature

When enabled in config (`offscreen_reload = True`), pointing the gun off-screen with the trigger pressed will automatically fire the Custom Button A action (useful for reload in games).

## Hardware Gun Controller

### Pin Configuration (ESP32)

The Arduino firmware uses the following pins:

- **TRIGGER_PIN**: GPIO 4 (Main trigger)
- **SECONDARY_PIN**: GPIO 5 (Secondary button)
- **BTNEXT1_PIN**: GPIO 25 (Custom Button A)
- **BTNEXT2_PIN**: GPIO 32 (Custom Button B)
- **BTNEXT3_PIN**: GPIO 33 (Custom Button C)

### Serial Protocol

The ESP32 sends button events over serial at 115200 baud:
- Format: `BUTTON_NAME:STATE`
- States: `0` for DOWN (pressed), `1` for UP (released)
- Example: `TRIGGER:0`, `btnexA:1`

## Technical Details

### Detection Algorithm

The system uses a multi-stage detection pipeline:

1. **Grayscale Conversion**: Converts BGR frames to grayscale
2. **Gaussian Blur**: Applies 5x5 blur to reduce noise
3. **Thresholding**: Binary threshold to isolate white regions (configurable via color_tolerance)
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
- Check if the correct camera index is set in camera selection
- Ensure webcam drivers are installed
- Verify webcam is working with other applications
- Try different camera indices (0, 1, 2, etc.)

### Gun controller not connecting
- Check if ESP32 is connected via USB
- Verify correct COM port in Device Manager (Windows) or `/dev/tty*` (Linux)
- Ensure baudrate matches (115200)
- Check if the port is used by another application
- Set `port = AUTO` in config.ini for auto-detection

### Button mapping not working
- Verify button is physically connected to correct GPIO pin
- Check serial monitor in Arduino IDE for button events
- Ensure button mapping is saved in config.ini
- Try using the "Reset" button in button mapping screen

### Performance issues
- Reduce video resolution in camera settings
- Close other applications using the webcam
- Adjust morphological operation iterations in detector.py
- Increase `color_tolerance` if detection is too slow

### Detection not working
- Ensure screen has a clear white border
- Adjust `color_tolerance` in config.ini (try higher values)
- Check lighting conditions (bright, even lighting works best)
- Verify webcam is positioned correctly
- Try enabling color mask view to see what's being detected

## Notice to AI usage

This project is made with the assist of Devin AI, but only to help with cases in the homography transformation math that I have been stuck on for ages. I still did all the coding and testing myself.
AI usage is allowed on contributions, but always triple check before actually pushing the code!

## License

This project is licensed under [WTFPL](LICENSE) (Just do whatever you want with it, I don't care).

## Contributing

Contributions are always welcome for this little script! Feel free to submit issues or pull requests.
