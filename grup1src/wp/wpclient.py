# !/usr/bin/python3

from tkinter import *
from tkinter import messagebox
from socket import *
import sys
import threading
import json
import time


class App:
    def __init__(self):
        # Defaults
        HOST = "127.0.0.1"
        PORT = 6161

        if len(sys.argv) > 1:
            HOST = sys.argv[1]
            if len(sys.argv) > 2:
                PORT = int(sys.argv[2])
        
        self.contacts = []
        self.messages = []
        self.contactNotRead = {}
        
        self.msgui = None
        self.currentContact = None

        self.uiman = UIManager(self, self.lateInit)
        self.conn = Connection(HOST, PORT, self)
        self.conn.start()
        
        statusChecker = StatusChecker(self.conn, self)
        statusChecker.start()

        self.uiman.run()

    def lateInit(self):
        self.username = self.loadUsername()
        if self.username != None:
            self.conn.login(self.username)
            return

        self.loginui = PromptUI(self.onLoginClick, "Username", "Login")
        self.uiman.show(self.loginui)

    def onLogon(self, success):
        self.saveUsername()
        if success:
            self.mainui = MainUI(self.username, self.onAddContactClick,
                                 self.onUserSelected)
            self.loadMainUI()
        else:
            self.loginui = PromptUI(self.onLoginClick, "Username", "Login")
            self.uiman.show(self.loginui)

    def onAddContactRecv(self, contactName):
        self.contacts += [contactName]
        self.contactNotRead[contactName] = True
        self.saveContacts()
        self.loadMainUI()

    def onStatusRecv(self, contactName, status):
        if self.uiman.isActive(self.msgui):
            if self.msgui != None and self.msgui.contactName == contactName:
                if status:
                    self.msgui.updateStatus("Online")
                else:
                    self.msgui.updateStatus("Offline")

    def onMessageRecv(self, contactName, message, mtime):
        print("Message for " + contactName + ": " + message)
        if not contactName in self.contacts:
            self.conn.addContact(contactName)
        self.logMessage(self.username, contactName, message, mtime)
        if self.uiman.isActive(self.msgui):
            if self.msgui != None and self.msgui.contactName == contactName:
                self.msgui.addMessage(True, message, mtime)
                return
        self.contactNotRead[contactName] = True
        self.saveContacts()
        self.updateUIContacts()

    def onLoginClick(self, username):
        if username != "":
            self.username = username
            self.conn.login(self.username)

    def onAddContactClick(self):
        addcontactui = PromptUI(self.onAddContactSubmit, "Contact ID",
                                "Add Contact", self.loadMainUI)
        self.uiman.clear()
        self.uiman.show(addcontactui)

    def onAddContactSubmit(self, contactName):
        if contactName != "" and not contactName in self.contacts:
            self.conn.addContact(contactName)

    def onUserSelected(self, contactName):
        self.msgui = MessageUI(contactName, self.loadMainUI, self.onMessage)
        self.uiman.clear()
        self.uiman.show(self.msgui)
        self.conn.getStatus(contactName)
        self.msgui.loadMessages([
            msg for msg in self.messages
            if (msg['to'] == contactName and msg['from'] == self.username) or (
                msg['to'] == self.username and msg['from'] == contactName)
        ])
        self.currentContact = contactName
        self.contactNotRead[contactName] = False
        self.saveContacts()

    def onMessage(self, contactName, msg):
        currentTime = time.strftime("%H:%M")
        self.msgui.addMessage(False, msg, currentTime)
        self.logMessage(contactName, self.username, msg, currentTime)
        self.conn.sendMessage(contactName, msg, currentTime)

    def loadMainUI(self):
        self.currentContact = None
        self.loadContacts()
        self.loadMessages()
        self.uiman.clear()
        self.uiman.show(self.mainui)
        self.updateUIContacts()
    
    def updateUIContacts(self):
        if self.uiman.isActive(self.mainui):
            self.mainui.clearContacts()
            self.mainui.addContacts([contact + " *" if self.contactNotRead[contact] else contact for contact in self.contacts])

    def loadUsername(self):
        try:
            with open("login.txt") as f:
                for username in f:
                    return username
        except FileNotFoundError:
            return None
        return None

    def saveUsername(self):
        with open("login.txt", "w+", encoding="utf-8") as f:
            f.write(self.username)

    def loadContacts(self):
        self.contacts = []
        self.contactNotRead = {}
        try:
            with open("contacts.txt") as f:
                for line in f:
                    lineParts = line[:-1].split(" ") # contactName msgsNotRead
                    self.contacts += [lineParts[0]]
                    if lineParts[1] == "1":
                        self.contactNotRead[lineParts[0]] = True
                    else:
                        self.contactNotRead[lineParts[0]] = False
        except FileNotFoundError:
            return None
        return None

    def saveContacts(self):
        with open("contacts.txt", "w+", encoding="utf-8") as f:
            for contactName in self.contacts:
                if self.contactNotRead[contactName]:
                    f.write(contactName + " 1\n")
                else:
                    f.write(contactName + " 0\n")

    def logMessage(self, userto, userfrom, message, mtime):
        self.messages += [{'to': userto, 'from': userfrom, 'msg': message, 'time': mtime}]
        with open("messages.json", "w+", encoding="utf-8") as f:
            json.dump(self.messages, f)

    def loadMessages(self):
        try:
            with open("messages.json", "r+", encoding="utf-8") as f:
                self.messages = json.load(f)
        except FileNotFoundError:
            pass


class UIManager:
    def __init__(self, app, lateInit):
        self.app = app
        self.root = Tk()
        self.root.geometry("300x600")
        self.root.title("NeUygulaması")
        self.root.after(100, lateInit)
        self.root.protocol("WM_DELETE_WINDOW", self.onClosing)
    
    def onClosing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.app.conn.sock.close()
            self.root.destroy()
            sys.exit()
    
    def show(self, ui):
        ui.show(self.root)
        self.ui = ui

    def isActive(self, ui):
        return self.ui == ui

    def run(self):
        mainloop()

    def clear(self):
        widget_list = self.root.winfo_children()

        for item in widget_list:
            if item.winfo_children():
                widget_list.extend(item.winfo_children())

        for item in widget_list:
            item.pack_forget()


class MainUI:
    def __init__(self, username, cbAddContactClick, cbUserSelected):
        self.username = username
        self.cbAddContactClick = cbAddContactClick
        self.cbUserSelected = cbUserSelected

    def show(self, root):
        root.title(self.username)

        header = Frame(root)
        header.pack(side=TOP, fill=X)

        newContact = Button(header,
                            text="Add Contact",
                            command=self.cbAddContactClick)
        newContact.pack(side=LEFT)

        usernameLabel = Label(header, text=self.username)
        usernameLabel.pack(side=RIGHT)

        scrollbar = Scrollbar(root, width=2)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.contactList = Listbox(root, yscrollcommand=scrollbar.set)
        self.contactList.bind('<<ListboxSelect>>', self.onUserSelected)
        self.contactList.pack(side=LEFT, fill=BOTH, expand=True)

        scrollbar.config(command=self.contactList.yview)

    def onUserSelected(self, evt):
        w = evt.widget
        selection = w.curselection()
        if len(selection) > 0:
            contactName = w.get(selection).split(" ")[0]
            self.cbUserSelected(contactName)

    def clearContacts(self):
        self.contactList.delete(0, self.contactList.size() - 1)

    def addContacts(self, contacts):
        for contact in contacts:
            self.contactList.insert(END, contact)


class MessageUI:
    def __init__(self, contactName, cbBackClick, cbMsgSend):
        self.contactName = contactName
        self.cbBackClick = cbBackClick
        self.cbMsgSend = cbMsgSend
        self.statusText = StringVar()

    def show(self, root):
        # Header
        header = Frame(root)
        header.pack(side=TOP, fill=X)

        backBtn = Button(header, text="<", command=self.onBackClick)
        backBtn.pack(side=LEFT)

        headerRight = Frame(header)
        headerRight.pack(side=TOP, fill=X)

        contactLabel = Label(headerRight, text=self.contactName)
        contactLabel.pack(side=TOP)

        statusLabel = Label(headerRight, textvariable=self.statusText)
        statusLabel.pack(side=BOTTOM)

        # Body
        body = Frame(root)
        body.pack(side=TOP, expand=True, fill=BOTH)

        scrollbar = Scrollbar(body, width=5, bd=0, elementborderwidth=0)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.messageList = Text(body, yscrollcommand=scrollbar.set)
        self.messageList.pack(side=LEFT, fill=BOTH, expand=True)

        self.messageList.tag_configure('left',
                                       justify=LEFT,
                                       font=('Verdana', 10, 'normal'))
        self.messageList.tag_configure('right',
                                       justify=RIGHT,
                                       font=('Verdana', 10, 'normal'))
        self.messageList.tag_configure('timeleft',
                                       justify=LEFT,
                                       font=('Verdana', 8, 'normal'))
        self.messageList.tag_configure('timeright',
                                       justify=RIGHT,
                                       font=('Verdana', 8, 'normal'))

        scrollbar.config(command=self.messageList.yview)

        # Bottom
        footer = Frame(root)
        footer.pack(side=TOP, fill=X)

        self.entry = Entry(footer, bd=1)
        self.entry.bind("<Key>", self.onKeyDown)
        self.entry.pack(side=LEFT, fill=BOTH, expand=True)

        btn = Button(footer, text=">>", command=self.onBtnClick)
        btn.pack(side=RIGHT, fill=Y)

    def updateStatus(self, status):
        self.statusText.set(status)

    def addMessage(self, leftSide, msg, mtime):
        self.messageList.config(state=NORMAL)
        if leftSide:
            self.messageList.insert(END, msg + "\n", "left")
            self.messageList.insert(END, mtime + "\n\n", "timeleft")
        else:
            self.messageList.insert(END, msg + "\n", "right")
            self.messageList.insert(END, mtime + "\n\n", "timeright")
        self.messageList.config(state=DISABLED)
        self.messageList.see("end")
    
    def onKeyDown(self, event):
        if event.keycode == 13:
            self.onBtnClick()

    def onBackClick(self):
        self.cbBackClick()

    def onBtnClick(self):
        text = self.entry.get().strip()
        if text != "":
            self.cbMsgSend(self.contactName, text)
            self.entry.delete(0, len(self.entry.get()))

    def loadMessages(self, messages):
        for msg in messages:
            self.addMessage(msg['from'] == self.contactName, msg['msg'], msg['time'])


class PromptUI:
    def __init__(self, cbBtnClick, lblText, btnText, cbBackClick=None):
        self.lblText = lblText
        self.btnText = btnText
        self.cbBtnClick = cbBtnClick
        self.cbBackClick = cbBackClick

    def show(self, root):
        label = Label(root, text=self.lblText)
        label.pack(side=TOP)

        self.entry = Entry(root, bd=1)
        self.entry.pack(side=TOP)

        btn = Button(root, text=self.btnText, command=self.onBtnClick)
        btn.pack(side=TOP)

        if self.cbBackClick != None:
            btn2 = Button(root, text="<", command=self.onBackClick)
            btn2.pack(side=TOP)

    def onBtnClick(self):
        self.cbBtnClick(self.entry.get())

    def onBackClick(self):
        self.cbBackClick()


class Connection(threading.Thread):
    def __init__(self, ip, port, app):
        threading.Thread.__init__(self)

        self.app = app
        self.sock = socket()
        self.sock.connect((ip, port))
        self.lastCheck = 0

    def run(self):
        lastMsg = ''
        while True:
            try:
                msg = self.sock.recv(64).decode()
                if msg == None or msg == "":
                    return
            except ConnectionAbortedError:
                return
            
            lastMsg += msg
            while "\n" in lastMsg:
                msg = lastMsg[:lastMsg.find("\n")]
                lastMsg = lastMsg[len(msg)+1:]

                params = msg.split(" ")
                cmd = params[0]
                print(msg)

                if cmd == "LOGON":
                    self.app.onLogon(params[1] == "1")
                elif cmd == "ADD":
                    self.app.onAddContactRecv(params[1])
                elif cmd == "STATUS":
                    self.app.onStatusRecv(params[1], params[2] == "1")
                elif cmd == "MSG":
                    message = " ".join(params[3:])
                    self.app.onMessageRecv(params[1], message, params[2])

    def login(self, username):
        self.sock.send(username.encode())

    def addContact(self, contactName):
        self.sock.send(b"ADD " + contactName.encode())

    def getStatus(self, contactName):
        self.sock.send(b"STATUS " + contactName.encode())

    def sendMessage(self, contactName, message, mtime):
        print(">MSG " + contactName + " " + mtime + " " + message)
        self.sock.send(b"MSG " + contactName.encode() + b" " + mtime.encode() + b" " + message.encode())

class StatusChecker(threading.Thread):
    def __init__(self, conn, app):
        threading.Thread.__init__(self)

        self.conn = conn
        self.app = app
        self.lastCheck = 0

    def run(self):
        while self.conn.is_alive():
            if self.app.currentContact != None:
                self.conn.getStatus(self.app.currentContact)
            time.sleep(3)

App()
