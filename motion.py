import cv2
from ultralytics import YOLO

# ================= CONFIGURATION =================
# 🔴 YOUR SPECIFIC IP ADDRESS
ESP32_IP = "192.168.0.119"
STREAM_URL = f"http://{ESP32_IP}:81/stream"
# =================================================

def main():
    print("Loading AI Model (this may take a moment)...")
    # Load the YOLOv8 model (It downloads automatically the first time)
    model = YOLO('yolov8n.pt') 

    print(f"Connecting to Camera at {STREAM_URL}...")
    cap = cv2.VideoCapture(STREAM_URL)

    if not cap.isOpened():
        print("❌ ERROR: Could not connect to camera!")
        return

    print("✅ Connected! Watching for Humans... (Press 'q' to quit)")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Stream ended or failed.")
            break

        # 1. Run the AI on the current frame
        # stream=True makes it faster
        results = model(frame, stream=True, verbose=False, classes=[0]) 
        # classes=[0] tells it to ONLY look for 'Person' (ID 0) and ignore everything else.

        # 2. Draw the results
        for r in results:
            annotated_frame = r.plot() # This draws the boxes and labels automatically
            
            # Display the video
            cv2.imshow("ESP32 Human Detector", annotated_frame)

        # Quit control
        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
