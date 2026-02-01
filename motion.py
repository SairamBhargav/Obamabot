import cv2
import numpy as np
from ultralytics import YOLO
from threading import Thread
import time

# ================= CONFIGURATION =================
ESP32_IP = "192.168.0.119"
STREAM_URL = f"http://{ESP32_IP}:81/stream"
SKIP_FRAMES = 3
GAMMA_LEVEL = 1.5 
# =================================================

class VideoStream:
    """
    This class runs in a separate thread. 
    It constantly grabs frames to empty the buffer 
    so you always get the latest image (low latency).
    """
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        Thread(target=self.update, args=()).start()
        return self

    def update(self):
        while True:
            if self.stopped:
                return
            # Grab the next frame
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        # Return the most recent frame
        return self.frame

    def stop(self):
        self.stopped = True
        self.stream.release()

def adjust_gamma(image, gamma=1.0):
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255
        for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(image, table)

def main():
    print("Loading AI Model...")
    # NOTE: If this is still too slow, change 'yolov8s.pt' back to 'yolov8n.pt'
    model = YOLO('yolov8s.pt') 

    print(f"Connecting to {STREAM_URL}...")
    
    # 🔴 Start the Threaded Video Stream
    vs = VideoStream(STREAM_URL).start()
    # Give the camera a second to warm up
    time.sleep(2.0)

    print("✅ Connected! (Press 'q' to quit)")

    frame_count = 0
    current_boxes = [] 

    while True:
        # Get the latest frame from the thread (Instant!)
        frame = vs.read()

        if frame is None:
            print("No frame received. Stopping.")
            break

        # Resize for AI (Keep display frame big)
        ai_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        ai_frame = adjust_gamma(ai_frame, gamma=GAMMA_LEVEL)

        # === AI LOGIC ===
        if frame_count % SKIP_FRAMES == 0:
            results = model(ai_frame, stream=True, verbose=False, classes=[0], conf=0.25)
            current_boxes = []
            for r in results:
                for box in r.boxes.data.tolist():
                    current_boxes.append(box)
        
        frame_count += 1

        # === DRAWING ===
        for box in current_boxes:
            x1, y1, x2, y2, conf, cls = box
            scale = 2 
            x1, y1, x2, y2 = int(x1*scale), int(y1*scale), int(x2*scale), int(y2*scale)
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            label = f"Human {int(conf*100)}%"
            t_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(frame, (x1, y1 - t_size[1] - 5), (x1 + t_size[0], y1), (0, 255, 0), -1)
            cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        cv2.imshow("Zero Lag Detector", frame)

        if cv2.waitKey(1) == ord('q'):
            break

    vs.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
