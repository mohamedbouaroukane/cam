import cv2
from pyzbar.pyzbar import decode
import socket

def scan_qr():
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        decoded_objects = decode(frame)
        
        for obj in decoded_objects:
            qr_data = obj.data.decode('utf-8')
            send_to_raspberry_pi(qr_data)
        
        cv2.imshow('QR Scanner', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

def send_to_raspberry_pi(data):
    host = '192.168.11.167'
    port = 12345
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    client_socket.send(data.encode('utf-8'))
    client_socket.close()

scan_qr()