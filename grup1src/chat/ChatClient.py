import socket
import threading

HOST_NAME = socket.gethostname()
IP_ADDRESS = socket.gethostbyname(HOST_NAME)
PORT = 6161


class ChatClient:
    def __init__(self, host, port, user_name):
        self.host = host
        self.port = port
        self.user_name = user_name
        self.client_socket = None

    def connect_server(self):
        self.client_socket = socket.socket()
        self.client_socket.connect((self.host, self.port))
        self.client_socket.send(self.user_name.encode())
        message = ""
        wait_message = WaitMessage(self.client_socket)
        wait_message.start()
        while message.lower() != "q":
            message = input()
            self.client_socket.send(message.encode())
        self.client_socket.send(message.encode())
        self.client_socket.close()


class WaitMessage(threading.Thread):
    def __init__(self, client_socket):
        threading.Thread.__init__(self)
        self.client_socket = client_socket

    def run(self):
        while True:
            try:
                incoming_message = self.client_socket.recv(1024).decode()
                print(incoming_message)
            except Exception as ex:
                break


if __name__ == '__main__':
    usr_name = input("User Name : ")
    ChatClient(IP_ADDRESS, PORT, usr_name).connect_server()
