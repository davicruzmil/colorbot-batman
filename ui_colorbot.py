import time
import socket
import struct
import os
import sys
import subprocess
import cv2
import numpy as np
import win32api
from mss import mss
import tkinter as tk

class MainFunction:
    def __init__(self):
        self.hardware = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.header = (0x12345678, 0)
        self.find_hardware()

    def deactivate(self):
        self.sock = None
        return

    def find_hardware(self):
        currentDir = sys._MEIPASS if getattr(sys, '_MEIPASS', None) else 'data'
        mapper = os.path.join(currentDir, 'Mapper.exe')
        driver = os.path.join(currentDir, 'mouseMoveDriver.sys')
        command = f"{mapper} {driver}"
        subprocess.run("sc stop faceit", shell=True)
        time.sleep(1)
        try:
            self.sock.connect(('localhost', 6666))
        except:
            input("Driver\nError loading the driver, make sure using Windows 10 and Secure Boot off.")
            os._exit(1)

    def move(self, x, y, click="0"):
        try:
            memory_data = (int(x * MOVE_SPEED), int(y * MOVE_SPEED), 0)
            self.send_packet(self.header + memory_data)
            if click != "0":
                self.shoot()
        except Exception as e:
            print(f"Error in move method: {e}")

    def shoot(self):
        self.send_packet(self.header + (0, 0, 0x1))
        time.sleep(0.001)
        self.send_packet(self.header + (0, 0, 0x2))

    def send_packet(self, packet_data):
        packet_bytes = struct.pack('IIiii', *packet_data)
        self.sock.send(packet_bytes)

class Capture:
    def __init__(self, x, y, xfov, yfov):
        self.mss = mss()
        self.monitor = {'top': y, 'left': x, 'width': xfov, 'height': yfov}
        self.xfov = xfov
        self.yfov = yfov

    def get_screen(self):
        screenshot = self.mss.grab(self.monitor)
        return np.array(screenshot)

class Colorbot:
    def __init__(self, x, y, xfov, yfov):
        self.mouse = MainFunction()
        self.grabber = Capture(x, y, xfov, yfov)
        self.last_position = None

    def listen(self):
        while True:
            if win32api.GetAsyncKeyState(0xA0) < 0:
                self.process()

    def process(self):
        screen = self.grabber.get_screen()
        hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, COLOR_LOWER, COLOR_UPPER)
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(mask, kernel, iterations=5)
        thresh = cv2.threshold(dilated, 60, 255, cv2.THRESH_BINARY)[1]
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        if contours:
            screen_center = (self.grabber.xfov // 2, self.grabber.yfov // 2)
            min_distance = float('inf')
            closest_contour = None

            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                center = (x + w // 2, y + h // 2)
                distance = ((center[0] - screen_center[0]) ** 2 + (center[1] - screen_center[1]) ** 2) ** 0.5

                if distance < min_distance:
                    min_distance = distance
                    closest_contour = contour

            if closest_contour is not None:
                x, y, w, h = cv2.boundingRect(closest_contour)
                center = (x + w // 2, y + h // 2)
                cX = center[0]
                cY = y + 10
                x_diff = cX - screen_center[0]
                y_diff = cY - screen_center[1]

                if self.last_position is None or (abs(x_diff) > MOVE_THRESHOLD or abs(y_diff) > MOVE_THRESHOLD):
                    print(f"Roxo detectado em: ({cX}, {cY})")
                    self.mouse.move(x_diff, y_diff)
                    self.last_position = (cX, cY)

def start_colorbot_interface():
    # Variáveis de configuração
    global FOV_SIZE, MOVE_THRESHOLD, MOVE_SPEED, COLOR_LOWER, COLOR_UPPER
    FOV_SIZE = 100
    MOVE_THRESHOLD = 15
    MOVE_SPEED = 0.6
    COLOR_LOWER = np.array([145, 130, 130])
    COLOR_UPPER = np.array([165, 255, 255])

    # Funções para a interface gráfica
    def update_config():
        global FOV_SIZE, MOVE_THRESHOLD, MOVE_SPEED
        FOV_SIZE = int(fov_entry.get())
        MOVE_THRESHOLD = int(threshold_entry.get())
        MOVE_SPEED = float(speed_entry.get())

    # Configuração da interface gráfica
    root = tk.Tk()
    root.title("Colorbot Config")
    root.geometry("300x200")
    root.configure(bg="#000000")  # Cor de fundo preta

    # Rótulos e entradas para configurações
    fov_label = tk.Label(root, text="FOV Size:", fg="#FFFFFF", bg="#000000")
    fov_label.grid(row=0, column=0, padx=10, pady=10)
    fov_entry = tk.Entry(root)
    fov_entry.insert(0, str(FOV_SIZE))
    fov_entry.grid(row=0, column=1, padx=10, pady=10)

    threshold_label = tk.Label(root, text="Move Threshold:", fg="#FFFFFF", bg="#000000")
    threshold_label.grid(row=1, column=0, padx=10, pady=10)
    threshold_entry = tk.Entry(root)
    threshold_entry.insert(0, str(MOVE_THRESHOLD))
    threshold_entry.grid(row=1, column=1, padx=10, pady=10)

    speed_label = tk.Label(root, text="Move Speed:", fg="#FFFFFF", bg="#000000")
    speed_label.grid(row=2, column=0, padx=10, pady=10)
    speed_entry = tk.Entry(root)
    speed_entry.insert(0, str(MOVE_SPEED))
    speed_entry.grid(row=2, column=1, padx=10, pady=10)

    # Botão de atualização das configurações
    update_button = tk.Button(root, text="Update Config", command=update_config, bg="#0000FF", fg="#FFFFFF")
    update_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

    root.mainloop()

    # Iniciar o bot após fechar a interface gráfica
    screen_width, screen_height = 1920, 1080
    x = (screen_width // 2) - (FOV_SIZE // 2)
    y = (screen_height // 2) - (FOV_SIZE // 2)
    xfov = FOV_SIZE
    yfov = FOV_SIZE

    bot = Colorbot(x, y, xfov, yfov)
    bot.listen()

start_colorbot_interface()
