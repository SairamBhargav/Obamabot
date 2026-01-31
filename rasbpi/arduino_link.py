import serial
import time
import cv2
import pyttsx3

# ---------------------------
# SERIAL SETUP
# ---------------------------
SERIAL_PORT = "/dev/ttyUSB0"  # Adjust if your Arduino is on a different port
BAUD_RATE = 115200
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)  # Wait for Arduino to initialize

# ---------------------------
# MOTOR COMMAND FUNCTION
# ---------------------------
def send_motor_cmd(l_speed, r_speed, l_dir, r_dir):
    cmd = f"{l_speed},{r_speed},{l_dir},{r_dir}\n"
    ser.write(cmd.encode())

# ---------------------------
# TEXT-TO-SPEECH SETUP
# ---------------------------
engine = pyttsx3.init()
def speak(text):
    engine.say(text)
    engine.runAndWait()

# ---------------------------
# CAMERA & HUMAN DETECTION
# ---------------------------
cap = cv2.VideoCapture(0)

# Load OpenCV pre-trained pedestrian detector
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

# Distance threshold (approx. bounding box height in pixels)
STOP_HEIGHT = 200  # Adjust based on your camera setup
BACKWARD_TIME = 2  # Seconds to back up

# ---------------------------
# MAIN LOOP
# ---------------------------
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        # Detect people in the frame
        boxes, weights = hog.detectMultiScale(frame, winStride=(8,8))
        
        if len(boxes) > 0:
            # Pick the largest detected person (closest)
            largest_box = max(boxes, key=lambda b: b[3])  # b[3] = height
            x, y, w, h = largest_box

            # Draw rectangle for debugging
            cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)
            
            # Check distance (based on bounding box height)
            if h < STOP_HEIGHT:
                # Drive forward
                send_motor_cmd(50, 50, 1, 1)
            else:
                # Stop and speak
                send_motor_cmd(0, 0, 1, 1)
                speak("Hello there!")  # Customize your message
                time.sleep(0.5)
                
                # Drive backward for safety
                send_motor_cmd(50, 50, 0, 0)
                time.sleep(BACKWARD_TIME)
                send_motor_cmd(0, 0, 1, 1)  # Stop after backing up
                break  # End loop (optional)
        else:
            # No person detected, stop motors
            send_motor_cmd(0, 0, 1, 1)

        # Optional: show camera for debugging
        cv2.imshow("Frame", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    send_motor_cmd(0, 0, 1, 1)
    ser.close()
