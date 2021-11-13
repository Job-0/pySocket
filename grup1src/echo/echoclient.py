import socket

HOST = socket.gethostname()
PORT = 6161

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    mesaj = ""
    while mesaj != "q":
        mesaj = input("Mesaj: ")
        s.send(mesaj.encode())
        data = s.recv(1024).decode()
        print("Alınan: ", data)