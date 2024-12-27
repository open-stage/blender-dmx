#    Copyright vanous
#
#    This file is part of BlenderDMX.
#
#    BlenderDMX is free software: you can redistribute it and/or modify it
#    under the terms of the GNU General Public License as published by the Free
#    Software Foundation, either version 3 of the License, or (at your option)
#    any later version.
#
#    BlenderDMX is distributed in the hope that it will be useful, but WITHOUT
#    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#    FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
#    more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program. If not, see <https://www.gnu.org/licenses/>.

import socket
import json
from threading import Thread
from queue import Queue
import time
import selectors
from datetime import datetime
from ...mvrxchange.mvr_message import mvr_message
from ...logging import DMX_Log

class client(Thread):
    """MVR TCP client, it is instanced via blender specific DMX_MVR_X_Client class located in mvrx_protocol.py"""

    def __init__(self, ip_address, port, callback, timeout=None, application_uuid=0):
        Thread.__init__(self, name=f"client {int(datetime.now().timestamp())}")
        DMX_Log.log.debug(self.name)
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
        DMX_Log.log.info("reconnecting")
        self.sel.unregister(sock)
        self.sel.close()
        self.socket.close()
        self.sel = selectors.DefaultSelector()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect_ex((self.ip_address, self.port))
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(self.socket, events)

    def disconnect(self, sock):
        DMX_Log.log.info("disconnecting")
        self.sel.unregister(sock)
        self.sel.close()
        self.socket.close()

    def join_mvr(self):
        self.send(mvr_message.create_message("MVR_JOIN", uuid=self.application_uuid))

    def leave_mvr(self):
        self.send(mvr_message.create_message("MVR_LEAVE", uuid=self.application_uuid))

    def request_file(self, commit, path):
        self.filepath = path
        self.commit = commit
        if commit.self_requested:  # we need to provide empty UUID in this case
            commit_uuid = ""
        else:
            commit_uuid = commit.commit_uuid
        self.send(mvr_message.create_message("MVR_REQUEST", uuid=commit.station_uuid, file_uuid=commit_uuid))
        #self.send(mvr_message.create_message("MVR_REQUEST", uuid=self.application_uuid, file_uuid=commit_uuid))

    def stop(self):
        self.running = False
        if self.socket is not None:
            self.sel.close()
            self.socket.close()
        self.join()

    def send(self, message):
        DMX_Log.log.debug(f"Send message {message}")
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
                                DMX_Log.log.debug(f"Received {recv_data!r}")
                                data += recv_data
                                if data:
                                    header = mvr_message.parse_header(data)
                                    if header["Error"]:
                                        data = b""

                                    if len(data) >= header["Total_len"]:
                                        total_len = header["Total_len"]
                                        DMX_Log.log.debug("go to parsing")
                                        self.parse_data(data[:total_len], self.callback)
                                        data = data[total_len:]

                        if not recv_data:
                            # self.disconnect(sock)
                            return

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

    def parse_data(self, data, callback):
        DMX_Log.log.debug(f"parsing {data}")
        header = mvr_message.parse_header(data)
        if header["Type"] == 0:  # json
            json_data = json.loads(data[28:].decode("utf-8"))
            callback(json_data)
        else:  # file
            with open(self.filepath, "bw") as f:
                f.write(data[28:])
            callback({"file_downloaded": self.commit, "StationUUID": self.commit.station_uuid})
