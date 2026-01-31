import cv2
from ultralytics import YOLO

# ================= CONFIGURATION =================
ESP32_IP = "192.168.0.119"
STREAM_URL = f"http://{ESP32_IP}:81/stream"

# SKIP_FRAMES: Higher number = Faster speed, but slightly more delay in updates
# Try 2, 3, or 5.
SKIP_FRAMES = 3 
# =================================================

def main():
    print("Loading AI Model...")
    model = YOLO('yolov8n.pt') 

    print(f"Connecting to {STREAM_URL}...")
    cap = cv2.VideoCapture(STREAM_URL)

    if not cap.isOpened():
        print("❌ ERROR: Could not connect to camera!")
        return

    print("✅ Connected! (Press 'q' to quit)")

    frame_count = 0
    last_results = None  # To store the boxes between AI checks

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Stream error.")
            break

        # RESIZE: Smaller images process MUCH faster.
        # We resize the display/processing frame to 640x480 max.
        frame = cv2.resize(frame, (640, 480))

        # === OPTIMIZATION: Only run AI every X frames ===
        if frame_count % SKIP_FRAMES == 0:
            # Run YOLO, but ONLY look for Persons (class 0)
            # conf=0.4 means "I need to be 40% sure it's a human"
            results = model(frame, stream=True, verbose=False, classes=[0], conf=0.4)
            
            # We have to iterate the generator to get the result object
            for r in results:
                last_results = r
        
        frame_count += 1

        # === DRAWING ===
        # If we have results from the last AI check, draw them now
        if last_results:
            # Plot returns the frame with boxes drawn on it
            display_frame = last_results.plot() 
            cv2.imshow("Fast Human Detector", display_frame)
        else:
            # If AI hasn't run yet, just show the raw frame
            cv2.imshow("Fast Human Detector", frame)

        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
