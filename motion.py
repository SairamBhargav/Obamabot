import cv2
import numpy as np
from ultralytics import YOLO

# ================= CONFIGURATION =================
ESP32_IP = "192.168.0.119"
STREAM_URL = f"http://{ESP32_IP}:81/stream"

# SKIP_FRAMES: We need to skip more frames because the new AI is heavier/smarter
SKIP_FRAMES = 4 

# GAMMA: Controls how much we brighten the dark areas (1.0 = normal, 2.5 = very bright shadows)
GAMMA_LEVEL = 1.5 
# =================================================

def adjust_gamma(image, gamma=1.0):
    # This function boosts the visibility of darker pixels
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255
        for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(image, table)

def main():
    print("Loading Upgrade AI Model (yolov8s)... this takes a second...")
    # Switched from 'n' (nano) to 's' (small). 's' is much more accurate.
    model = YOLO('yolov8s.pt') 

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

        # === 1. PREPARE IMAGE FOR AI ===
        # Resize small for speed
        ai_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        
        # 🔴 CRITICAL FIX: GAMMA CORRECTION
        # This brightens the image significantly for the AI so it can see faces
        # that usually get hidden in shadow.
        ai_frame = adjust_gamma(ai_frame, gamma=GAMMA_LEVEL)

        # === 2. AI DETECTION ===
        if frame_count % SKIP_FRAMES == 0:
            # conf=0.20: Low threshold to catch everyone
            results = model(ai_frame, stream=True, verbose=False, classes=[0], conf=0.20)
            
            current_boxes = []
            for r in results:
                for box in r.boxes.data.tolist():
                    current_boxes.append(box)
        
        frame_count += 1

        # === 3. DRAWING ON ORIGINAL FRAME ===
        for box in current_boxes:
            x1, y1, x2, y2, conf, cls = box
            
            # Scale coordinates back up (x2 because we resized by 0.5)
            scale = 2 
            x1, y1, x2, y2 = int(x1*scale), int(y1*scale), int(x2*scale), int(y2*scale)
            
            # Draw Box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw Label
            label = f"Human {int(conf*100)}%"
            t_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(frame, (x1, y1 - t_size[1] - 5), (x1 + t_size[0], y1), (0, 255, 0), -1)
            cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        # Show the normal video (we don't show the gamma-boosted one because it looks washed out)
        cv2.imshow("Pro Human Detector", frame)
        
        # Optional: Uncomment this to see what the AI sees (The brightened version)
        # cv2.imshow("AI Vision (Debug)", ai_frame)

        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
