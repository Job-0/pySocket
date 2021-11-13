import socket

HOST = socket.gethostname()
PORT = 6161

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soket:
    soket.bind((HOST, PORT))
    soket.listen()
    print("Client bağlantısı bekleniyor...")
    conn, cl_addr = soket.accept();
    with conn:
        print("Bağlantı adresi: ", cl_addr)
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break
            conn.send(data.encode())
            print("Mesaj gönderildi ---> ", data)