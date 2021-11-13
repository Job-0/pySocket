#!/usr/bin/env python3

import socket
import sys
import re
import os

BUFFER_SIZE = 1024
SERVER_NAME = 'CENG-Server'
MESSAGES = {
    200: 'OK',
    400: 'Bad Request',
    404: 'Not Found',
    405: 'Method Not Allowed',
    500: 'Internal Server Error'
}

re_startline = re.compile(r'^(\w+) (.+) HTTP/1\.[01]$')
re_path_clean = re.compile(r'/+(?=/)|\.+(?=\.)|(?<=/)\./')
re_path = re.compile(r'^/([a-zA-Z0-9\._ \t\-]+/)*[a-zA-Z0-9\._ \t\-]*$')

def main():
    args = parseArgs()

    print('Starting the server on %s:%d' % (args['host'], args['port']))

    # Soketi oluştur
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Dinlemeye başla
        sock.bind((args['host'], args['port']))
        sock.listen()

        print('Waiting for clients...')
        while True:
            # İstemciyi kabul et
            conn, addr = sock.accept()
            if not conn:
                continue
            
            # İstemciye cevap ver
            processRequest(conn, addr) # TODO threading ekle?

def parseArgs():
    argc = len(sys.argv)
    host = ''
    port = 8080

    if argc > 1:
        if sys.argv[1] == '-h':
            printUsage()
        
        host = sys.argv[1]
        
        if argc > 2:
            try:
                port = int(sys.argv[0])
            except ValueError as err:
                printUsage()
    
    return {
        'host': host,
        'port': port
    }


def printUsage():
    print('Usage: %s [HOST] [PORT]' % (sys.argv[0]))
    sys.exit(1)

def processRequest(conn, addr):
    # Header ve Body boşluğuna gelene kadar oku
    data = recvUntil(conn, b'\r\n\r\n')

    # Okunan veriyi satırlara ayır
    lines = data.split(b'\r\n')
    startline = lines[0] # İlk satır

    if lines[-1] != b'': # Son satır \r\n olmalı
        print('# Unexpected EOF', addr)
        conn.close()
        return

    # İlk satırı düzenli ifadeler ile kontrol et
    m = re_startline.match(startline.decode('utf-8'))
    if not m:
        print('# Invalid start line', addr)
        sendHeader(conn, 400, 0)
        conn.close()
        return

    # Sadece GET metoduna izin ver
    method = m.group(1)
    if method != 'GET':
        print('# Invalid method', addr)
        sendHeader(conn, 405, 0)
        conn.close()
        return

    # Yolu kontrol et
    path = cleanPath(m.group(2))
    if not isValidPath(path):
        print('# Invalid path', addr)
        sendHeader(conn, 400, 0)
        conn.close()
        return
    
    print('# Request for %s from' % (path), addr)

    if path == '/':
        # Programın bulunduğu klasördeki dosyaları listele
        sendFileList(conn)
    else:
        sendFile(conn, addr, path[1:])

    conn.close()

def recvUntil(conn, stopstr):
    line = conn.recv(BUFFER_SIZE)
    data = line
    while stopstr not in line:
        line = conn.recv(BUFFER_SIZE)
        data += line
    
    return data

def sendHeader(conn, code, length, ctype='text/html'):
    headers  = 'HTTP/1.1 %d %s\r\n' % (code, MESSAGES[code])
    headers += 'Server: %s\r\n' % (SERVER_NAME)
    headers += 'Content-Type: %s\r\n' % (ctype)
    headers += 'Content-Length: %d\r\n' % (length)
    headers += '\r\n'
    
    return conn.sendall(headers.encode('utf-8'))

def cleanPath(path):
    return re_path_clean.sub('', path)

def isValidPath(path):
    return re_path.match(path) != None

def sendFileList(conn):
    files = os.listdir('.')
    
    data = b'<h1>Dosyalar:</h1><ul>'
    for f in files:
        data += ('<li><a href="/%s">%s</a></li>' % (f, f)).encode('utf-8')
    data += b'</ul>'

    sendHeader(conn, 200, len(data))
    conn.sendall(data)

def sendFile(conn, addr, fpath, code=200):
    try:
        data = readFile(fpath)
        
        if fpath[-5:] != '.html':
            sendHeader(conn, code, len(data), 'text/plain')
        else:
            sendHeader(conn, code, len(data))
        
        conn.sendall(data)
    except FileNotFoundError: # Dosya bulunamadı
        if code == 404:
            sendHeader(conn, 404, 0)
        else:
            sendFile(conn, addr, '404.html', 404)
            print('# Path Not Found', addr)
    except Exception as e: # Bir hata oluştu
        if code == 500:
            sendHeader(conn, 500, 0)
        else:
            sendFile(conn, addr, '500.html', 500)
            print('# Error for', addr, e)

def readFile(fn):
    with open(fn, 'rb') as f:
        line = f.read(1024)
        data = line
        while line:
            line = f.read(1024)
            data += line
    return data

if __name__ == '__main__':
    main()
