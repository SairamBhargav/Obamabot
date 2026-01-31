import cv2
import numpy as np

ESP32_IP = "192.168.0.119"  # <--- EDIT THIS!
# ==========================================

STREAM_URL = f"http://{ESP32_IP}:81/stream"

def main():
    print(f"Connecting to: {STREAM_URL} ...")
    cap = cv2.VideoCapture(STREAM_URL)

    if not cap.isOpened():
        print("❌ ERROR: Could not connect to camera!")
        print("   Make sure you are on the same WiFi as the ESP32.")
        return

    print("✅ Connected! Press 'q' to quit. Press 'r' to reset background.")

    static_back = None

    while True:
        # Get frame from stream
        ret, frame = cap.read()
        if not ret:
            print("Frame error (stream might have stopped)")
            break

        # Resize for speed (optional)
        frame = cv2.resize(frame, (640, 480))
        
        # specific processing for motion detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # Initialize the "background" (first frame)
        if static_back is None:
            static_back = gray
            continue

        # Compute difference (Motion = Difference between Now and Background)
        diff_frame = cv2.absdiff(static_back, gray)
        thresh_frame = cv2.threshold(diff_frame, 30, 255, cv2.THRESH_BINARY)[1]
        thresh_frame = cv2.dilate(thresh_frame, None, iterations=2)

        # Find the shapes of the movement
        cnts, _ = cv2.findContours(thresh_frame.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in cnts:
            if cv2.contourArea(contour) < 1000: # Ignore tiny movements
                continue
            
            # Draw the box
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Add text
            cv2.putText(frame, "MOTION DETECTED", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Show the video
        cv2.imshow("ESP32 Feed", frame)

        # Keyboard controls
        key = cv2.waitKey(1)
        if key == ord('q'): 
            break
        if key == ord('r'): # 'r' resets the background reference
            static_back = gray
            print("Background reset!")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()