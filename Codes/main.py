"""
ARDUINO UNO Q - PYTHON SIDE (MPU / Linux side)
App Lab folder: python/main.py

This script does NOT perform any camera/OpenCV operations.
Its only tasks are:
  1. Start a TCP socket server on the WiFi network
  2. When an 'R' or 'B' command is received from the PC (VS Code),
     send it directly to the Arduino sketch's
     "pick_and_place" function using Bridge.call()
  3. Send the result back to the PC

This allows your PC (where OpenCV is already running correctly)
and the board (where the servo motors are connected) to
communicate through WiFi - no USB/COM port serial connection is required.
"""

from arduino.app_utils import *
import socket
import threading

HOST = "0.0.0.0"     # Listens on all network interfaces
PORT = 5005           # The same port number must be used in the PC client code

COLOR_MAP = {
    "R": 1,   # RED
    "B": 2,   # BLUE
}


def handle_client(conn, addr):
    print("=" * 40)
    print(f"[CONNECT] PC connected from {addr}")
    with conn:
        while True:
            try:
                data = conn.recv(16)
            except (ConnectionResetError, OSError) as e:
                print(f"[DISCONNECT] Connection lost: {e}")
                break

            if not data:
                print("[DISCONNECT] PC closed connection")
                break

            command = data.decode(errors="ignore").strip().upper()
            print(f"[RECEIVED] Raw data from PC: '{command}'")

            if command in COLOR_MAP:
                color_code = COLOR_MAP[command]
                print(f"[BRIDGE] Calling pick_and_place({color_code}) on Arduino sketch...")

                try:
                    result = Bridge.call("pick_and_place", color_code)
                    print(f"[BRIDGE] Arduino returned: {result}")
                except Exception as e:
                    print(f"[BRIDGE ERROR] Bridge.call failed: {e}")
                    result = "BRIDGE_ERROR"

                conn.sendall(str(result).encode())
                print(f"[SENT] Sent '{result}' back to PC")
            else:
                print(f"[WARNING] Unknown command '{command}' ignored")
                conn.sendall(b"UNKNOWN_CMD")
    print("=" * 40)


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[SERVER] Socket server started successfully.")
    print(f"[SERVER] Listening on {HOST}:{PORT} - waiting for PC to connect...")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


def loop():
    # The socket server is running in a separate thread,
    # so there is nothing to do inside loop().
    pass


# Start the socket server in a background thread,
# then give control to App.run() (Bridge manages this)
threading.Thread(target=start_server, daemon=True).start()
App.run(user_loop=loop)