import os
import socket
import selectors
import types
import json
import struct
from threading import Thread
from uuid import uuid4
import time
from datetime import datetime
from dmx.mvrxchange.mvr_message import mvr_message
from dmx.logging import DMX_Log


class server(Thread):
    def __init__(self, callback, uuid=str(uuid4())):
        Thread.__init__(self, name=f"server {int(datetime.now().timestamp())}")
        DMX_Log.log.debug(self.name)
        self.uuid = uuid
        self.running = True
        self.callback = callback
        self.sel = selectors.DefaultSelector()
        self.lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.lsock.bind(("", 0))
        self.port = self.lsock.getsockname()[1]
        self.lsock.listen()
        DMX_Log.log.debug(f"Listening on {self.port}, {uuid}")
        self.lsock.setblocking(False)
        self.sel.register(self.lsock, selectors.EVENT_READ, data=None)
        self.files = []

    def stop(self):
        self.running = False
        if self.lsock is not None:
            self.sel.close()
            self.lsock.close()
        self.join()

    def accept_wrapper(self, sock):
        conn, addr = sock.accept()  # Should be ready to read
        DMX_Log.log.debug(f"Accepted connection from {addr}")
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=[], file_uuid="")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, data=data)

    def get_port(self):
        return self.port

    def parse_data(self, data):
        DMX_Log.log.debug(f"parse data {data}")
        header = mvr_message.parse_header(data.inb)
        if header["Type"] == 0:  # json
            json_data = json.loads(data.inb[28:].decode("utf-8"))
            self.process_json_message(json_data, data)
        else:  # file
            local_path = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(local_path, "mvrs", f"{data.file_uuid}.mvr")
            DMX_Log.log.debug("writing file")
            with open(path, "bw") as f:
                f.write(data.inb[28:])
            # time.sleep(0.1)
            # json_data["StationUUID"] = self.uuid
            # for client in self.sel.select():
            #    client[0].data.outb = mvr_message.craft_packet(json_data)

    def service_connection(self, key, mask):
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Should be ready to read
            if recv_data:
                data.inb += recv_data
                DMX_Log.log.debug(("server received", len(data.inb), data.inb, data.addr, "\n"))
                header = mvr_message.parse_header(data.inb)
                DMX_Log.log.debug(f"header {header}")
                if header["Error"]:
                    DMX_Log.log.error(f"error {data.inb}")
                    data.inb = b""
                elif len(data.inb) >= header["Total_len"]:
                    total_len = header["Total_len"]
                    left_over = data.inb[total_len:]
                    DMX_Log.log.debug(f"go to parsing {left_over}")
                    data.inb = data.inb[:total_len]
                    self.parse_data(data)
                    data.inb = left_over
            else:
                DMX_Log.log.debug(f"Closing connection to {data.addr}")
                self.sel.unregister(sock)
                sock.close()
        if mask & selectors.EVENT_WRITE:
            if len(data.outb):
                msg = data.outb.pop(0)
                DMX_Log.log.debug("send msg" + str(msg))  # strange, but logger didn't want to convert it via f-strings
                header = mvr_message.parse_header(msg)
                if not header["Error"]:
                    DMX_Log.log.debug("Reply" + str(msg))  # same here
                sock.sendall(msg)  # Should be ready to write
                # sent = sock.send(data.outb)  # Should be ready to write
                # data.outb = data.outb[sent:]

    def process_json_message(self, json_data, data):
        DMX_Log.log.debug(f"Json message {json_data} {data}")
        self.callback(json_data, data)
        if json_data["Type"] == "MVR_JOIN":
            data.outb.append(mvr_message.create_message("MVR_JOIN_RET", ok="false", nok_reason="Not accepting connections at this point", uuid = self.uuid))
            # data.outb.append(mvr_message.create_message("MVR_JOIN_RET"))
        if json_data["Type"] == "MVR_LEAVE":
            data.outb.append(mvr_message.create_message("MVR_LEAVE_RET", uuid=self.uuid))
        if json_data["Type"] == "MVR_COMMIT":
            data.outb.append(mvr_message.create_message("MVR_COMMIT_RET", uuid=self.uuid))

        if json_data["Type"] == "MVR_REQUEST":
            # Leaving this here for the future
            local_path = os.path.dirname(os.path.abspath(__file__))
            file_uuid = json_data["FileUUID"]
            file_path = os.path.join(local_path, "mvrs", f"{file_uuid}.mvr")
            DMX_Log.log.debug("sending file")
            if not os.path.exists(file_path):
                file_uuid = "B905D390-A281-11EE-BA6D-A0595013B622"
                file_path = os.path.join(local_path, "mvrs", f"{file_uuid}.mvr")

            file_size = os.path.getsize(file_path)
            file_object = open(file_path, "br")
            buffer = file_object.read(1024)
            data.outb.append(mvr_message.craft_packet(None, file_size, buffer, 1))
            buffer = file_object.read(1024)
            while buffer:
                data.outb.append(buffer)
                buffer = file_object.read(1024)
            file_object.close()

    def run(self):
        while self.running:
            events = self.sel.select(timeout=1)
            for key, mask in events:
                if key.data is None:
                    self.accept_wrapper(key.fileobj)
                else:
                    self.service_connection(key, mask)
        # self.sel.close()


if __name__ == "__main__":
    serve = server()
    serve.start()
