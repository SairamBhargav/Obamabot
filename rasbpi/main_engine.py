import threading
import time
import serial
import random
import os
from flask import Flask, jsonify, url_for

# --- CONFIGURATION ---
# Check ports with 'ls /dev/tty*' after plugging them in
ESP32_PORT = '/dev/ttyUSB0'  # The Eyes
XRP_PORT   = '/dev/ttyACM0'  # The Muscles (might be ttyUSB1 or serial0 depending on connection)

# Robot Settings
TARGET_FACE_WIDTH = 110  # Roasting distance (Bigger # = Closer)
CENTER_X = 160           # Middle of image
DEADZONE = 40            # Don't turn if face is within this center range

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
    global roast_queue
    try:
        eyes = serial.Serial(ESP32_PORT, 115200, timeout=0.1)
        muscles = serial.Serial(XRP_PORT, 9600, timeout=1)
        time.sleep(2) # Allow connections to settle
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
                    center = int(parts[1])
                    width = int(parts[2])
                    
                    print(f"Target: X={center} W={width}")

                    # LOGIC TREE
                    if width >= TARGET_FACE_WIDTH:
                        print(">>> ROASTING!")
                        muscles.write(b'S') # Stop
                        
                        # Pick random roast
                        files = [f for f in os.listdir('static') if f.endswith('.mp3')]
                        if files:
                            roast_queue = url_for('static', filename=random.choice(files))
                        
                        time.sleep(6) # Wait for audio to finish
                        
                    elif center < (CENTER_X - DEADZONE):
                        muscles.write(b'L') # Turn Left
                    elif center > (CENTER_X + DEADZONE):
                        muscles.write(b'R') # Turn Right
                    else:
                        muscles.write(b'F') # Forward

        except Exception as e:
            print(f"Loop Error: {e}")

if __name__ == '__main__':
    t = threading.Thread(target=robot_brain)
    t.daemon = True
    t.start()
    app.run(host='0.0.0.0', port=5000, debug=False)