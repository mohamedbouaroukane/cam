import socket

def receive_data():
    host = '0.0.0.0'
    port = 12345
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    
    print("Waiting for QR data...")
    
    while True:
        client_socket, address = server_socket.accept()
        data = client_socket.recv(1024).decode('utf-8')
        print(f"Received QR data: {data}")
        client_socket.close()

receive_data()