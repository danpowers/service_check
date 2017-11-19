#!/usr/bin/python

from threading import Thread
from Queue import Queue
import SocketServer
import datetime
import argparse
import socket
import csv

class ConnectionHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(1024).strip()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        hostname = self.client_address[0]
        expected_reply_string = "GridFTP Server"
        unexpected_reply_exception = "Unexpected GridFTP Banner"

        if self.server.myproxy:
            expected_reply_string = "MYPROXY"
            unexpected_reply_exception = "Unexpected MyProxy Reply"

        try:
            try:
                port = int(self.data)
            except Exception as e:
                port = str(self.data)
                raise Exception("Bad port value " + port)
            s.connect((hostname, port))
            if self.server.myproxy:
                s.sendall("hello")
            reply = s.recv(4096).strip()
            if not expected_reply_string in reply:
                raise Exception(unexpected_reply_exception)
            self.request.sendall("Scan of " + str(hostname) + ":" + str(port) + " successful.\n")
            self.server.logger_queue.put((datetime.datetime.utcnow(), hostname, port, "success", "none"))
        except Exception as e:
            self.request.sendall("Scan of " + str(hostname) + ":" + str(port) + " failed: " + str(e) + "\n")
            self.server.logger_queue.put((datetime.datetime.utcnow(), hostname, port, "fail", e))

        try:
            s.shutdown(socket.SHUT_RDWR)
            s.close()
        except Exception as e:
            pass

class LogWriter(Thread):
    def __init__(self,logger_queue,logfile):
        Thread.__init__(self)
        self.logger_queue = logger_queue
        self.logfile = logfile

    def run(self):
        with open(self.logfile, 'ab+') as outputfile:
            csvOutputFileWriter = csv.writer(outputfile, delimiter=',')
            while True:
                time, host, port, result, msg = self.logger_queue.get()
                csvOutputFileWriter.writerow([time.strftime("%H:%M:%S %d-%m-%Y"), host, port, result, msg])
                outputfile.flush()
                self.logger_queue.task_done()

def parse_arguments():
    p = argparse.ArgumentParser()
    p.add_argument("-m", "--myproxy", action="store_true", help="run myproxy check service")
    p.add_argument("-g", "--gridftp", action="store_true", help="run gridftp check service")
    a = p.parse_args()

    if (a.gridftp and a.myproxy) or (not a.gridftp and not a.myproxy):
        p.print_help()
        exit(0)

    return a

def main():
    args = parse_arguments()
    logger_queue = Queue()
    hostname, port = "0.0.0.0", 50000
    logfile = "gridftp_check_log.csv"

    if args.myproxy:
        port = 50001
        logfile = "myproxy_check_log.csv"

    logger_thread = LogWriter(logger_queue, logfile)
    logger_thread.setDaemon(True)
    logger_thread.start()

    server = SocketServer.ThreadingTCPServer((hostname, port), ConnectionHandler)
    server.logger_queue = logger_queue
    server.myproxy = args.myproxy
    server.gridftp = args.gridftp
    server.serve_forever()

if __name__ == "__main__":
    main()
