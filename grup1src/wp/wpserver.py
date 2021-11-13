# !/usr/bin/python3

from socket import *
import threading
import sys

class Client(threading.Thread):
    def __init__(self, sock, srv):
        threading.Thread.__init__(self)
        self.sock = sock
        self.username = None
        self.srv = srv

    def run(self):
        try:
            while True:
                self.username = self.sock.recv(64).decode()
                if self.username != "":
                    if not self.username in self.srv.userlist:
                        self.srv.userlist += [self.username]
                        self.srv.saveUserList()

                    if not self.username in self.srv.clients:
                        self.srv.clients[self.username] = self
                        break
        except ConnectionResetError:
            pass
        
        print("User connected: " + self.username)
        self.sock.sendall(b"LOGON 1\n")

        msgs = self.srv.getPendingMessages(self.username)
        for msg in msgs:
            self.sendMessage(msg['from'], msg['msg'], msg['time'])
        self.srv.clearPendingMessages(self.username)

        while True:
            try:
                msg = self.sock.recv(1024)
                if msg == None or msg == b"":
                    print("Disconnected " + self.username)
                    break
            except ConnectionResetError:
                print("Disconnected " + self.username)
                break

            params = msg.decode().split(" ")
            cmd = params[0]
            print(msg)

            if cmd == "ADD":
                contactName = params[1]
                if contactName in self.srv.userlist:
                    self.sock.sendall(b"ADD " + contactName.encode() + b'\n')
            elif cmd == "STATUS":
                contactName = params[1]
                if contactName in self.srv.clients:
                    self.sock.sendall(b"STATUS " + contactName.encode() + b" 1\n")
                else:
                    self.sock.sendall(b"STATUS " + contactName.encode() + b" 0\n")
            elif cmd == "MSG":
                contactName = params[1]
                message = " ".join(params[3:])
                if contactName in self.srv.clients:
                    if self.srv.clients[contactName].sendMessage(
                        self.username, message, params[2]):
                        continue
                
                self.srv.addPendingMessage(contactName, self.username, message, params[2])
        
        del self.srv.clients[self.username]

    def sendMessage(self, contactName, message, mtime):
        try:
            self.sock.send(b"MSG " + contactName.encode() + b" " + mtime.encode() + b" " + message.encode() + b'\n')
            return True
        except ConnectionResetError:
            del self.srv.clients[self.username]
        return False


class Server:
    def __init__(self):
        self.clients = {}
        self.pendingMsgs = {}
        self.loadUserList()
        
        # Defaults
        HOST = "127.0.0.1"
        PORT = 6161

        if len(sys.argv) > 1:
            HOST = sys.argv[1]
            if len(sys.argv) > 2:
                PORT = int(sys.argv[2])

        with socket() as sock:
            sock.bind((HOST, PORT))
            sock.listen()
            
            print("Listening for connections...")

            while True:
                csock, addr = sock.accept()
                cli = Client(csock, self)
                cli.start()

    def addPendingMessage(self, userto, userfrom, message, mtime):
        if not userto in self.pendingMsgs:
            self.pendingMsgs[userto] = []
        self.pendingMsgs[userto] += [{'from': userfrom, 'msg': message, 'time': mtime}]

    def getPendingMessages(self, username):
        if username in self.pendingMsgs:
            return self.pendingMsgs[username]
        return []

    def clearPendingMessages(self, username):
        if username in self.pendingMsgs:
            del self.pendingMsgs[username]

    def loadUserList(self):
        self.userlist = []
        try:
            with open("userlist.txt") as f:
                for username in f:
                    self.userlist += [username]
        except FileNotFoundError:
            return None
        return None

    def saveUserList(self):
        with open("userlist.txt", "w") as f:
            for username in self.userlist:
                f.write(username + "\n")


Server()
