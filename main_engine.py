import threading
import time
import serial
import random
import os
from flask import Flask, jsonify, url_for

# --- CONFIGURATION ---
# Check ports with 'ls /dev/tty*' after plugging them in
#
# ESP32_PORT is the serial port connected to your ESP32 camera module (the
# "eyes"), which streams face tracking information in the format
#   FACE:<center_x>:<width>
#
# XRP_PORT is the serial port connected to the XRP robot board (the
# "muscles").  This board expects single character commands: 'F', 'B', 'L',
# 'R', 'S' as documented in xrp_serial_drive.ino.  The default baud rate
# matches the Arduino sketch (115200).
ESP32_PORT = '/dev/ttyUSB0'  # The eyes
XRP_PORT   = '/dev/ttyACM0'  # The muscles (might be ttyUSB1 or serial0 depending on connection)

# Robot settings
# TARGET_FACE_WIDTH defines how large a detected face must be before the robot
# stops and plays a random roast.  Increase this value to wait for closer
# faces, decrease it to react sooner.
TARGET_FACE_WIDTH = 110
# CENTER_X is the centre of the camera’s field of view (in pixels).
CENTER_X = 160
# DEADZONE defines a range about CENTER_X where the robot won’t turn.  This
# prevents oscillations when the face is roughly centred.
DEADZONE = 40

app = Flask(__name__)
roast_queue = None

# --- WEB SERVER (THE MOUTH) ---
@app.route('/')
def index():
    return """
    <html>
    <body style="background:black; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;">
        <img src="/static/face.jpg" style="height:100%; object-fit:contain;" onclick="document.body.requestFullscreen()">
        <script>
            setInterval(() => {
                fetch('/poll').then(r => r.json()).then(data => {
                    if(data.play) new Audio(data.play).play();
                });
            }, 1000);
        </script>
    </body>
    </html>
    """

@app.route('/poll')
def poll():
    global roast_queue
    if roast_queue:
        url = roast_queue
        roast_queue = None
        return jsonify({'play': url})
    return jsonify({'play': None})

# --- ROBOT LOGIC (THE BRAIN) ---
def robot_brain():
    """Main loop coordinating sensor input and motor output."""
    global roast_queue
    try:
        # Open serial ports
        eyes = serial.Serial(ESP32_PORT, 115200, timeout=0.1)
        # Use the same baud rate as the Arduino sketch (115200)
        muscles = serial.Serial(XRP_PORT, 115200, timeout=1)
        time.sleep(2)  # Allow connections to settle
        print("SYSTEM ONLINE.")
    except Exception as e:
        print(f"HARDWARE ERROR: {e}")
        return

    while True:
        try:
            if eyes.in_waiting:
                line = eyes.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith("FACE:"):
                    parts = line.split(':')
                    if len(parts) < 3:
                        continue
                    center = int(parts[1])
                    width = int(parts[2])

                    print(f"Target: X={center} W={width}")

                    # Decision tree for robot actions
                    if width >= TARGET_FACE_WIDTH:
                        print(">>> ROASTING!")
                        muscles.write(b'S')  # Stop

                        # pick a random audio file from the static folder
                        files = [f for f in os.listdir('static') if f.lower().endswith('.mp3')]
                        if files:
                            roast_queue = url_for('static', filename=random.choice(files))
                        # wait long enough for the audio to play before continuing
                        time.sleep(6)

                    elif center < (CENTER_X - DEADZONE):
                        muscles.write(b'L')  # Turn left
                    elif center > (CENTER_X + DEADZONE):
                        muscles.write(b'R')  # Turn right
                    else:
                        muscles.write(b'F')  # Forward

        except Exception as e:
            # report but continue; transient serial errors may occur
            print(f"Loop Error: {e}")


if __name__ == '__main__':
    # run the robot logic in a background thread so Flask remains responsive
    t = threading.Thread(target=robot_brain)
    t.daemon = True
    t.start()
    # run the web server on all interfaces without debug messages
    app.run(host='0.0.0.0', port=5000, debug=False)