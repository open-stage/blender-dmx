#!/bin/env python3

import socket
import json
from threading import Thread
import struct
from queue import Queue
import time
import selectors

# A very rudimentary MVR-xchange client
# For some reason, some apps close the socket, so we must ensure to reconnect


class client(Thread):
    def __init__(self, ip_address, port, callback, timeout=None, application_uuid=0):
        Thread.__init__(self)
        self.callback = callback
        self.running = True
        self.queue = Queue()
        self.ip_address = ip_address
        self.application_uuid = application_uuid
        self.port = port
        self.filepath = ""
        self.commit = ""
        self.sel = selectors.DefaultSelector()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setblocking(False)
        self.socket.connect_ex((ip_address, port))
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(self.socket, events)
        # if timeout is not None and self.socket is not None:
        #    self.socket.settimeout(timeout)

    def reconnect(self, sock):
        print("reconnecting")
        self.sel.unregister(sock)
        self.sel.close()
        self.socket.close()
        self.sel = selectors.DefaultSelector()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect_ex((self.ip_address, self.port))
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(self.socket, events)

    def join_mvr(self):
        self.send(self.join_message())

    def leave_mvr(self):
        self.send(self.leave_message())

    def request_file(self, commit, path):
        self.filepath = path
        self.commit = commit
        self.send(self.request_message(commit.commit_uuid))

    def stop(self):
        self.running = False
        if self.socket is not None:
            self.sel.close()
            self.socket.close()
        self.join()

    def send(self, message):
        self.queue.put(message)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.modify(self.socket, events)

    def run(self):
        data = b""

        while self.running:
            events = self.sel.select(timeout=1)
            if events:
                for key, mask in events:
                    sock = key.fileobj
                    if mask & selectors.EVENT_READ:
                        try:
                            recv_data = sock.recv(1024)  # Should be ready to read
                        except BlockingIOError:
                            pass
                        else:
                            if recv_data:
                                print(f"Received {recv_data!r}")
                                data += recv_data
                                if data:
                                    header = self.parse_header(data)
                                    if header["error"]:
                                        data = b""

                                    if len(data) >= header["total_len"]:
                                        total_len = header["total_len"]
                                        print("go to parsing")
                                        self.parse_data(data[:total_len], self.callback)
                                        data = data[total_len:]

                        if not recv_data:
                            self.reconnect(sock)

                    if not self.queue.empty():
                        if mask & selectors.EVENT_WRITE:
                            message = self.queue.get()
                            if message:
                                sock.sendall(message)

                            if self.queue.empty():
                                events = selectors.EVENT_READ
                                self.sel.modify(self.socket, events)

                    if data == b"":
                        time.sleep(0.2)

    def parse_header(self, data):
        header = {"error": True}
        if len(data) > 4:
            if struct.unpack("!l", data[0:4])[0] == 778682:
                msg_version = struct.unpack("!l", data[4:8])[0]
                msg_number = struct.unpack("!l", data[8:12])[0]
                msg_count = struct.unpack("!l", data[12:16])[0]
                msg_type = struct.unpack("!l", data[16:20])[0]
                msg_len = struct.unpack("!q", data[20:28])[0]
                header = {"version": msg_version, "number": msg_number, "count": msg_count, "type": msg_type, "data_len": msg_len, "total_len": msg_len + 28, "error": False}
        return header

    def parse_data(self, data, callback):
        print("parsing", data)
        header = self.parse_header(data)
        if header["type"] == 0:  # json
            json_data = json.loads(data[28:].decode("utf-8"))
            callback(json_data)
        else:  # file
            with open(self.filepath, "bw") as f:
                f.write(data[28:])
            callback({"file_downloaded": self.commit, "StationUUID": self.commit.station_uuid})

    def join_message(self):
        return self.craft_packet(
            {
                "Type": "MVR_JOIN",
                "Provider": "Blender DMX",
                "verMajor": 1,
                "verMinor": 6,
                "StationUUID": self.application_uuid,
                "StationName": "Blender DMX Station",
                "Files": [],
            }
        )

    def leave_message(self):
        return self.craft_packet(
            {
                "Type": "MVR_LEAVE",
                "FromStationUUID": self.application_uuid,
            }
        )

    def request_message(self, uuid):
        return self.craft_packet(
            {
                "Type": "MVR_REQUEST",
                "FileUUID": f"{uuid}",
                "FromStationUUID": self.application_uuid,
            }
        )

    def craft_packet(self, message):
        MVR_PACKAGE_HEADER = 778682
        MVR_PACKAGE_VERSION = 1
        MVR_PACKAGE_NUMBER = 0
        MVR_PACKAGE_COUNT = 1
        MVR_PACKAGE_TYPE = 0
        MVR_PAYLOAD_BUFFER = json.dumps(message).encode("utf-8")
        MVR_PAYLOAD_LENGTH = len(MVR_PAYLOAD_BUFFER)

        output = (
            struct.pack("!l", MVR_PACKAGE_HEADER)
            + struct.pack("!l", MVR_PACKAGE_VERSION)
            + struct.pack("!l", MVR_PACKAGE_NUMBER)
            + struct.pack("!l", MVR_PACKAGE_COUNT)
            + struct.pack("!l", MVR_PACKAGE_TYPE)
            + struct.pack("!q", MVR_PAYLOAD_LENGTH)
            + MVR_PAYLOAD_BUFFER
        )
        return output
