import sys
import threading
import time
from PyQt5 import QtWidgets, QtCore
from lockercontrol.lockerControl import LockerController
from ui.main import MainApp
from barcodeScanner import qr_scanner
from communication.communicationModule import HttpRequester
import socket
from signature.signature import decrypt_and_verify

class QRScannerThread(QtCore.QThread):
    scanner_stopped = QtCore.pyqtSignal()
    qr_code_success = QtCore.pyqtSignal(str)  # Signal for successful QR code
    qr_code_failed = QtCore.pyqtSignal(str)   # Signal for failed QR code scan

    def __init__(self, http_requester):
        super().__init__()
        self.http_requester = http_requester

    def run(self):
        while True:
            try:
                self.receive_data(self.http_requester)
            except Exception as e:
                print(f"QR scanner stopped: {e}")
                self.scanner_stopped.emit()
                break

    def receive_data(self, http_requester):
        host = '0.0.0.0'
        port = 12345
        
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(1)
        
        print("Waiting for QR data...")
        
        while True:
            client_socket, address = server_socket.accept()
            try:
                data = client_socket.recv(1024).decode('utf-8')
                print(f"Received QR data: {data}")
                decrypted_data, valid = decrypt_and_verify(data)
                print(f"Validation result: {valid}")
                
                if valid:
                    http_requester.send_request(decrypted_data)
                    self.qr_code_success.emit(decrypted_data)
                else:
                    # Emit signal for invalid QR code
                    self.qr_code_failed.emit("Invalid QR Code: Verification Failed")
            except Exception as e:
                # Emit signal for any scanning or decryption errors
                self.qr_code_failed.emit(f"Scan Error: {str(e)}")
            finally:
                client_socket.close()            

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = MainApp.getInstance()
        self.ui.show()
        self.http_requester = HttpRequester("http://localhost:8080/api/v1/")
        self.connect_signals()
        self.create_success_dialog()
        self.create_error_dialog()
        self.start_qr_scanner()

    def create_success_dialog(self):
        # Success Dialog
        self.success_dialog = QtWidgets.QDialog(self)
        self.success_dialog.setWindowTitle("QR Code Scanned")
        self.success_dialog.setFixedSize(400, 300)
        
        layout = QtWidgets.QVBoxLayout()
        
        # Success label
        success_label = QtWidgets.QLabel("QR Code Successfully Scanned!")
        success_label.setStyleSheet("""
            font-size: 20px;
            color: green;
            font-weight: bold;
            padding: 20px;
            text-align: center;
        """)
        success_label.setAlignment(QtCore.Qt.AlignCenter)
        
        # Details label (will show QR code data)
        self.success_details_label = QtWidgets.QLabel()
        self.success_details_label.setStyleSheet("""
            font-size: 16px;
            padding: 10px;
            text-align: center;
        """)
        self.success_details_label.setAlignment(QtCore.Qt.AlignCenter)
        
        layout.addWidget(success_label)
        layout.addWidget(self.success_details_label)
        
        self.success_dialog.setLayout(layout)

    def create_error_dialog(self):
        # Error Dialog
        self.error_dialog = QtWidgets.QDialog(self)
        self.error_dialog.setWindowTitle("QR Code Error")
        self.error_dialog.setFixedSize(400, 300)
        
        layout = QtWidgets.QVBoxLayout()
        
        # Error label
        error_label = QtWidgets.QLabel("QR Code Scan Failed!")
        error_label.setStyleSheet("""
            font-size: 20px;
            color: red;
            font-weight: bold;
            padding: 20px;
            text-align: center;
        """)
        error_label.setAlignment(QtCore.Qt.AlignCenter)
        
        # Error details label
        self.error_details_label = QtWidgets.QLabel()
        self.error_details_label.setStyleSheet("""
            font-size: 16px;
            color: darkred;
            padding: 10px;
            text-align: center;
        """)
        self.error_details_label.setAlignment(QtCore.Qt.AlignCenter)
        
        layout.addWidget(error_label)
        layout.addWidget(self.error_details_label)
        
        self.error_dialog.setLayout(layout)

    def connect_signals(self):
        self.http_requester.show_courier_access_signal.connect(self.ui.show_courier_access)
        self.http_requester.show_collect_parcel_signal.connect(self.ui.show_collect_parcel)
        self.http_requester.error_signal.connect(self.show_error_message)

    def show_error_message(self, message):
        QtWidgets.QMessageBox.critical(self, "Error", message)

    def start_qr_scanner(self):
        self.qr_thread = QRScannerThread(self.http_requester)
        self.qr_thread.scanner_stopped.connect(self.on_scanner_stopped)
        self.qr_thread.qr_code_success.connect(self.show_qr_success_dialog)
        self.qr_thread.qr_code_failed.connect(self.show_qr_error_dialog)  # New connection
        self.qr_thread.start()

    def show_qr_success_dialog(self, qr_data):
        # Update details label with QR code data
        self.success_details_label.setText(f"Data: {qr_data}")
        
        # Show the success dialog
        self.success_dialog.show()
        
        # Close dialog after 5 seconds
        QtCore.QTimer.singleShot(5000, self.success_dialog.close)

    def show_qr_error_dialog(self, error_message):
        # Update error details label
        self.error_details_label.setText(f"{error_message}")
        
        # Show the error dialog
        self.error_dialog.show()
        
        # Close dialog after 5 seconds
        QtCore.QTimer.singleShot(5000, self.error_dialog.close)

    def on_scanner_stopped(self):
        reply = QtWidgets.QMessageBox.question(
            self, 'QR Scanner Stopped', 
            "QR Scanner has stopped. Do you want to restart it?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, 
            QtWidgets.QMessageBox.Yes
        )
        if reply == QtWidgets.QMessageBox.Yes:
            self.start_qr_scanner()
        else:
            self.close()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

    
