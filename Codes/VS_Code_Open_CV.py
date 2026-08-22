"""
VS CODE (PC) SIDE - OpenCV Object Detection + WiFi Command Sender
-------------------------------------------------------------------
This code runs on your PC/laptop in VS Code. The camera is also
connected to the PC. Whenever a RED or BLUE object is detected
anywhere in the COMPLETE camera frame (there is no center-zone
restriction), the board (Uno Q) receives an 'R' or 'B' command
through the WiFi network. The board then moves the arm and places
the object accordingly.
(This part is handled by python/main.py + sketch.ino running on
the board through App Lab).


Requirements (install on PC):
    pip install opencv-python numpy


Run:
    python object_sort_client.py
"""


import cv2
import numpy as np
import socket
import time


# ------------------------------------------------------
# Enter the IP address of the Uno Q board here.
# How to find it:
#   1) Connect the board in App Lab, open the "Console",
#      and run the command: hostname -I
#   2) Or check your WiFi router's admin page (such as
#      192.168.1.1) and look for the connected device
#      named "arduino" / "uno-q".
# ------------------------------------------------------
ARDUINO_IP = "192.168.1.68"    # Match this with your board's IP address
ARDUINO_PORT = 5005             # Must match the port set in main.py


CAMERA_INDEX = 0
MIN_CONTOUR_AREA = 800


# Use a smaller resolution to reduce lag
FRAME_WIDTH = 480
FRAME_HEIGHT = 360


# Cooldown (in seconds) to prevent repeated commands for the same object
COMMAND_COOLDOWN = 3.0


RED_LOWER1 = np.array([0, 120, 70])
RED_UPPER1 = np.array([10, 255, 255])
RED_LOWER2 = np.array([170, 120, 70])
RED_UPPER2 = np.array([180, 255, 255])


BLUE_LOWER = np.array([94, 120, 70])
BLUE_UPPER = np.array([126, 255, 255])




def send_command(command):
    """Sends a command to the board and returns its response."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(10)
            sock.connect((ARDUINO_IP, ARDUINO_PORT))
            sock.sendall(command.encode())
            response = sock.recv(64).decode(errors="ignore")
            return response
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        print(f"Connection error: {e}")
        print("Check: 1) Are the board and PC on the same WiFi? "
              "2) Is ARDUINO_IP correct? 3) Is main.py running on the board?")
        return None




def get_largest_contour_center(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, None


    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < MIN_CONTOUR_AREA:
        return None, None


    M = cv2.moments(largest)
    if M["m00"] == 0:
        return None, None


    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])
    return (cx, cy), largest




def main():
    # CAP_DSHOW helps open/read the camera faster on Windows
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(CAMERA_INDEX)  # Fallback if DSHOW is unavailable


    if not cap.isOpened():
        print("Error: Camera could not be opened. Check CAMERA_INDEX.")
        return


    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)   # Skip old buffered frames to reduce lag


    ret, frame = cap.read()
    if not ret:
        print("Error: No frame received from the camera.")
        return


    arm_busy = False
    last_command_time = 0.0


    print("Object sorting started... Press 'q' to exit.")


    while True:
        ret, frame = cap.read()
        if not ret:
            break


        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)


        red_mask1 = cv2.inRange(hsv, RED_LOWER1, RED_UPPER1)
        red_mask2 = cv2.inRange(hsv, RED_LOWER2, RED_UPPER2)
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)
        blue_mask = cv2.inRange(hsv, BLUE_LOWER, BLUE_UPPER)


        kernel = np.ones((5, 5), np.uint8)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)
        blue_mask = cv2.morphologyEx(blue_mask, cv2.MORPH_OPEN, kernel)


        red_center, red_contour = get_largest_contour_center(red_mask)
        blue_center, blue_contour = get_largest_contour_center(blue_mask)


        detected_color = None
        obj_center = None


        if red_center is not None:
            obj_center = red_center
            detected_color = "R"
            cv2.drawContours(frame, [red_contour], -1, (0, 0, 255), 2)
            cv2.circle(frame, red_center, 6, (0, 0, 255), -1)
            cv2.putText(frame, "RED", (red_center[0] - 20, red_center[1] - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)


        elif blue_center is not None:
            obj_center = blue_center
            detected_color = "B"
            cv2.drawContours(frame, [blue_contour], -1, (255, 0, 0), 2)
            cv2.circle(frame, blue_center, 6, (255, 0, 0), -1)
            cv2.putText(frame, "BLUE", (blue_center[0] - 20, blue_center[1] - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)


        now = time.time()


        # Send a command when a color is detected anywhere in the frame.
        # There is no center-zone restriction. The cooldown prevents
        # the same object from triggering the command repeatedly.
        if (not arm_busy) and obj_center is not None and (now - last_command_time) >= COMMAND_COOLDOWN:
            print(f"{detected_color} object detected -> sending over WiFi")
            arm_busy = True


            response = send_command(detected_color)
            print("Board response:", response)


            last_command_time = time.time()
            arm_busy = False


        cv2.imshow("AI Garbage Sorter - Camera (PC side)", frame)


        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


    cap.release()
    cv2.destroyAllWindows()




if __name__ == "__main__":
    main()
