import cv2
import numpy as np
import serial
import time

# Serial communication setup (adjust the COM port and baud rate as needed)
esp = serial.Serial('COM12', 9600, timeout=1)  # Replace 'COM12' with your port

def rotate_servo():
    print("Rotating servo...")
    esp.write(b'1')  # Send a signal to rotate the servo
    time.sleep(5)    # Wait for 5 seconds
    esp.write(b'0')  # Stop the servo
    print("Servo stopped.")

def wait_for_motion():
    print("Waiting for motion detection...")
    while True:
        if esp.in_waiting > 0:
            motion = esp.readline().decode('utf-8').strip()
            if motion == 'motion_detected':
                print("Motion detected!")
                return

# Load YOLO
net = cv2.dnn.readNet("yolov3-tiny.weights", "yolov3-tiny.cfg")
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

# Load COCO class labels
with open("coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]

while True:
    wait_for_motion()  # Wait for motion detection

    # Initialize the camera (webcam)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not access the camera.")
        continue

    print("Camera turned on for 15 seconds...")
    start_time = time.time()
    dog_detected = False

    while time.time() - start_time < 15:
        # Capture frame-by-frame
        ret, frame = cap.read()

        if not ret:
            print("Failed to grab frame.")
            break

        # Resize frame for YOLO input
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        net.setInput(blob)
        outs = net.forward(output_layers)

        # Process detections
        class_ids = []
        confidences = []
        boxes = []

        height, width, channels = frame.shape

        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]

                if confidence > 0.5 and classes[class_id] == "dog":
                    # Get bounding box coordinates
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)

                    # Rectangle coordinates
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)

                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        # Apply Non-Maximum Suppression
        indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

        if len(indices) > 0:
            for i in indices.flatten():
                x, y, w, h = boxes[i]
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                label = f"{classes[class_ids[i]]} {confidences[i]:.2f}"
                cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                if classes[class_ids[i]] == "dog":
                    dog_detected = True

        # Display the resulting frame
        cv2.imshow("Dog Detection", frame)

        if dog_detected:
            print("Dog detected! Turning off the camera and rotating servo...")
            cap.release()  # Turn off the camera
            cv2.destroyAllWindows()
            rotate_servo()  # Rotate the servo motor for 5 seconds
            break

        # Break on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    if not dog_detected:
        print("Dog not detected. Turning off the camera.")
        cap.release()
        cv2.destroyAllWindows()
