import cv2
import numpy as np
from ultralytics import YOLO

# ================= CONFIGURATION =================
ESP32_IP = "192.168.0.119"
STREAM_URL = f"http://{ESP32_IP}:81/stream"

# Skip frames to keep speed high (3 is usually best)
SKIP_FRAMES = 3 
# =================================================

def apply_improvements(frame):
    # 1. CLAHE (Contrast Limited Adaptive Histogram Equalization)
    # This balances the light/dark areas so faces are visible even in shadow.
    # It converts to LAB color space, fixes the Light (L) channel, and merges back.
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

    # 2. SHARPENING
    # This kernel makes edges crisper (like glasses for the camera)
    kernel = np.array([[0, -1, 0],
                       [-1, 5,-1],
                       [0, -1, 0]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)
    
    return sharpened

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
    current_boxes = [] 

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Stream error.")
            break

        # Resize first (Speed)
        frame = cv2.resize(frame, (640, 480))

        # === 🔴 APPLY IMAGE ENHANCEMENTS ===
        # This fixes the lighting/blur so the AI can see EVERYONE better
        frame = apply_improvements(frame)

        # === AI DETECTION ===
        if frame_count % SKIP_FRAMES == 0:
            # conf=0.20: Lowered confidence so it catches people more easily
            results = model(frame, stream=True, verbose=False, classes=[0], conf=0.20)
            
            current_boxes = []
            for r in results:
                for box in r.boxes.data.tolist():
                    current_boxes.append(box)
        
        frame_count += 1

        # === DRAWING ===
        for box in current_boxes:
            x1, y1, x2, y2, conf, cls = box
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            
            # Draw Box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # Label
            cv2.putText(frame, "Person", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow("Enhanced Detector", frame)

        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
