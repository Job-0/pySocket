import socket
import threading

HOST = socket.gethostname()
PORT = 6161
clients = []


class ChatServer:
    def __init__(self):
        server_socket = socket.socket()
        try:
            server_socket.bind((HOST, PORT))
            server_socket.listen(4)
            print("waiting for a connection")
            while True:
                client_socket, address = server_socket.accept()
                print("starting connection to " + str(address))
                client_name = client_socket.recv(1024).decode()
                client = ServerThread(client_socket, address, client_name)
                clients.append(client)
                client.start()
        except Exception as ex:
            print(ex)
        finally:
            server_socket.close()


class ServerThread(threading.Thread):
    def __init__(self, client_socket, address, client_name):
        threading.Thread.__init__(self)
        self.client_socket = client_socket
        self.address = address
        self.client_name = client_name

    def run(self):
        while True:
            response = self.client_socket.recv(1024).decode()
            if response.lower() == "q":
                clients.remove(self)
                print("closing connection to" + str(self.client_socket.getpeername()))
                self.client_socket.close()
                break
            message = self.client_name + "-> " + response
            for client in clients:
                if client != self:
                    client.client_socket.send(message.encode())


if __name__ == '__main__':
    ChatServer()
