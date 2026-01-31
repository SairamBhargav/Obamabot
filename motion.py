import cv2
from ultralytics import YOLO

# ================= CONFIGURATION =================
ESP32_IP = "192.168.0.119"
STREAM_URL = f"http://{ESP32_IP}:81/stream"

# SKIP_FRAMES: 
# 3 is a sweet spot. It means AI runs 10 times a second (fast enough),
# while video runs at full speed (30+ FPS).
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
    # Store the box coordinates here: [x1, y1, x2, y2, confidence, class_id]
    current_boxes = [] 

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Stream error.")
            break

        # Resize for consistent speed
        frame = cv2.resize(frame, (640, 480))

        # === 1. AI DETECTION (Only runs every 3rd frame) ===
        if frame_count % SKIP_FRAMES == 0:
            # Run YOLO. classes=[0] checks only for 'person'
            # conf=0.25 is standard sensitivity
            results = model(frame, stream=True, verbose=False, classes=[0], conf=0.25)
            
            # Clear old boxes and save new ones
            current_boxes = []
            for r in results:
                # r.boxes.data contains [x1, y1, x2, y2, conf, cls]
                for box in r.boxes.data.tolist():
                    current_boxes.append(box)
        
        frame_count += 1

        # === 2. DRAWING (Runs EVERY frame) ===
        # We draw the "remembered" boxes onto the current live frame
        for box in current_boxes:
            x1, y1, x2, y2, conf, cls = box
            # Convert to integers for drawing
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            
            # Draw Red Box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            # Draw Label
            label = f"Human {conf:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        # Show the final image
        cv2.imshow("Fast Human Detector", frame)

        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
