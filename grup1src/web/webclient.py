#!/usr/bin/env python3

from urllib.parse import urlparse
import socket
import sys

BUFFER_SIZE = 1024
CLIENT_NAME = 'CENG-Client'

class URL:
    def __init__(self, host, port, path):
        self.host = host
        self.port = port
        self.path = path

def main():
    args = parseArgs()
    url = args['url']

    print('# Visiting http://%s:%d%s' % (url.host, url.port, url.path))

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((url.host, url.port))
        sock.sendall(buildRequest(url.host, url.path))

        data = sock.recv(BUFFER_SIZE)
        response = data
        while data:
            data = sock.recv(BUFFER_SIZE)
            response += data
        
        print('# Response from the server:')
        print(response.decode('utf-8'))

def parseArgs():
    if len(sys.argv) < 2 or sys.argv[1] == '':
        printUsage()

    return {
        'url': parseURL('http://' + sys.argv[1])
    }

def printUsage():
    print('Usage: %s [URL]\r\n\r\nURL: URL without scheme (e.g. example.com:8080/show/me/the/way)' % (sys.argv[0]))
    sys.exit(1)

def parseURL(url):
    u = urlparse(url)
    host = u.hostname
    port = u.port
    path = u.path
    
    if host == None:
        host =  '127.0.0.1'
    
    if port == None:
        port = 8080
    else:
        port = int(port)
    
    if path[:1] != '/':
        path = '/' + path

    return URL(host, port, path)

def buildRequest(host, path):
    s  = 'GET %s HTTP/1.1\r\n' % (path)
    s += 'Host: %s\r\n' % (host)
    s += 'User-Agent: %s\r\n' % (CLIENT_NAME)
    s += '\r\n'
    return s.encode('utf-8')

if __name__ == '__main__':
    main()
