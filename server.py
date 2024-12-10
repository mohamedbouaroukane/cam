import sys
import threading
import time
from PyQt5 import QtWidgets, QtCore
from lockercontrol.lockerControl import LockerController
from ui.main import MainApp
from barcodeScanner import qr_scanner
from communication.communicationModule import HttpRequester

class QRScannerThread(QtCore.QThread):
    scanner_stopped = QtCore.pyqtSignal()

    def __init__(self, http_requester):
        super().__init__()
        self.http_requester = http_requester

    def run(self):
        while True:
            try:
                qr_scanner(self.http_requester)
            except Exception as e:
                print(f"QR scanner stopped: {e}")
                self.scanner_stopped.emit()
                break

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = MainApp.getInstance()
        self.ui.show()
        self.http_requester = HttpRequester("http://localhost:8080/api/v1/")
        self.connect_signals()
        self.start_qr_scanner()

    def connect_signals(self):
        self.http_requester.show_courier_access_signal.connect(self.ui.show_courier_access)
        self.http_requester.show_collect_parcel_signal.connect(self.ui.show_collect_parcel)

        self.http_requester.error_signal.connect(self.show_error_message)

    def show_error_message(self, message):
        QtWidgets.QMessageBox.critical(self, "Error", message)

    def start_qr_scanner(self):
        self.qr_thread = QRScannerThread(self.http_requester)
        self.qr_thread.scanner_stopped.connect(self.on_scanner_stopped)
        self.qr_thread.start()

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

    
