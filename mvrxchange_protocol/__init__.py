#!/bin/env python3

import socket
import json
from threading import Thread
import struct
from queue import Queue
import time

# A very rudimentary MVR-xchange client
# The socket handling is lame at this point, reconnecting socket on every send (which is not often though)


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
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.connect((ip_address, port))
        if timeout is not None and self.socket is not None:
            self.socket.settimeout(timeout)

    def reconnect(self):
        print("reconnecting")
        self.socket.close()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ip_address, self.port))

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
            self.socket.close()
        self.join()

    def send(self, message):
        self.queue.put(message)

    def run(self):
        data = b""
        if self.socket is None:
            return
        while self.running:
            message = None
            try:
                new_data = self.socket.recv(1024)
                data += new_data
            except Exception as e:
                ...
            else:
                if data:
                    header = self.parse_header(data)
                    if header["error"]:
                        data = b""
                        continue

                    if len(data) >= header["total_len"]:
                        self.parse_data(data, self.callback)
                        data = b""

            if not self.queue.empty():
                message = self.queue.get()
                if message:
                    self.reconnect()
                    self.socket.sendall(message)

            if not data:
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
