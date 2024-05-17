import socket
import struct
import os
import sys
import subprocess
import cv2
import numpy as np
import win32api
from mss import mss
import json
import time
import requests
import hashlib
from keyauth import api
# Verifica se o arquivo config.json existe, se não existir, cria com valores padrão
if not os.path.exists("config.json"):
    with open("config.json", "w") as config_file:
        config = {
            "FOV_SIZE": 100,
            "MOVE_THRESHOLD": 15,
            "MOVE_SPEED": 0.6
        }
        json.dump(config, config_file, indent=4)

# Carrega as configurações do arquivo config.json
with open("config.json", "r") as config_file:
    config = json.load(config_file)
    FOV_SIZE = config.get("FOV_SIZE", 100)
    MOVE_THRESHOLD = config.get("MOVE_THRESHOLD", 15)
    MOVE_SPEED = config.get("MOVE_SPEED", 0.6)

# Verifica se o arquivo key.json existe, se não existir, cria com valor vazio
if not os.path.exists("key.json"):
    with open("key.json", "w") as key_file:
        key_data = {"key": ""}
        json.dump(key_data, key_file)

# Carrega a chave do arquivo key.json
with open("key.json", "r") as key_file:
    key_data = json.load(key_file)
    key = key_data.get("key", "")

def getchecksum():
    md5_hash = hashlib.md5()
    file = open(''.join(sys.argv), "rb")
    md5_hash.update(file.read())
    digest = md5_hash.hexdigest()
    return digest

# Verifica a chave KeyAuth
def check_key(chave):
    keyauthapp = api(
    name = "BatmanSpoofer", # Application Name
    ownerid = "xUAJqxfOK8", # Owner ID
    secret = "06181572c98a641c13f77f47f7eebbbeeb48d13e976268a76d2c9cf1517e93c9", # Application Secret
    version = "1.0", # Application Version
    hash_to_check = getchecksum()
    )
    keyauthapp.license(chave)
check_key(key)

COLOR_LOWER = np.array([145, 130, 130])
COLOR_UPPER = np.array([165, 255, 255])


class mainFunction:
    def __init__(self):
        self.hardware = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.header = (0x12345678, 0)
        self.findHardware()

    def deactivate(self):
        self.sock = None
        return

    def findHardware(self):
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
        self.mouse = mainFunction()
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


if __name__ == "__main__":
    screen_width, screen_height = 1920, 1080
    x = (screen_width // 2) - (FOV_SIZE // 2)
    y = (screen_height // 2) - (FOV_SIZE // 2)
    xfov = FOV_SIZE
    yfov = FOV_SIZE

    bot = Colorbot(x, y, xfov, yfov)
    bot.listen()
