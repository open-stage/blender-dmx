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

import json
import os
import selectors
import socket
import time
import types
from datetime import datetime
from queue import Queue
from threading import Thread
from uuid import uuid4

import bpy

from ..logging import DMX_Log
from .mvrx_message import mvrx_message


class server(Thread):
    """MVR TCP server for incoming connections, it is instanced via blender specific DMX_MVR_X_Server class located in mvrx_protocol.py"""

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

        self.commit = None
        self.filepath = None  # TODO: this will also need to be per connected client

        # allow Windows to get the port
        max_retries = 5
        retry_delay = 0.1
        for _ in range(max_retries):
            try:
                self.port = self.lsock.getsockname()[1]
                break
            except OSError:
                time.sleep(retry_delay)
                retry_delay = retry_delay * 2
        else:
            raise RuntimeError("Failed to get the port number")

        self.lsock.listen()
        DMX_Log.log.debug(f"Listening on {self.port}, {uuid}")
        self.lsock.setblocking(False)
        self.sel.register(self.lsock, selectors.EVENT_READ, data=None)
        self.files = []
        self.post_data = Queue()  # TODO: need a queue per service connection

    def stop(self):
        self.running = False
        if self.lsock is not None:
            self.sel.close()
            self.lsock.close()
        self.join()

    def set_post_data(self, data):
        DMX_Log.log.debug(f"Setting post data")
        self.post_data.put(data)

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
        header = mvrx_message.parse_header(data.inb)
        if header["Type"] == 0:  # json
            json_data = json.loads(data.inb[28:].decode("utf-8"))
            self.process_json_message(json_data, data)
        else:  # file
            dmx = bpy.context.scene.dmx
            DMX_Log.log.debug("writing file")
            with open(self.filepath, "bw") as f:
                f.write(data.inb[28:])
            dmx.fetched_mvr_downloaded_file(self.commit)

    def service_connection(self, key, mask):
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Should be ready to read
            if recv_data:
                data.inb += recv_data
                DMX_Log.log.debug(
                    ("server received", len(data.inb), data.inb, data.addr, "\n")
                )
                header = mvrx_message.parse_header(data.inb)
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
                DMX_Log.log.debug(
                    "send msg" + str(msg)
                )  # strange, but logger didn't want to convert it via f-strings
                header = mvrx_message.parse_header(msg)
                if not header["Error"]:
                    DMX_Log.log.debug("Reply" + str(msg))  # same here
                sock.sendall(msg)  # Should be ready to write
                # sent = sock.send(data.outb)  # Should be ready to write
                # data.outb = data.outb[sent:]

    def process_json_message(self, json_data, data):
        DMX_Log.log.debug(f"Json message {json_data} {data}")
        if json_data["Type"] == "MVR_JOIN":
            shared_commits = bpy.context.window_manager.dmx.mvr_xchange.shared_commits
            commits = []
            for commit in shared_commits:
                commit_template = mvrx_message.commit_message.copy()
                commit_template["FileSize"] = commit.file_size
                commit_template["FileUUID"] = commit.commit_uuid
                commit_template["StationUUID"] = self.uuid
                file_name = commit.file_name or commit.comment.replace(" ", "_")
                commit_template["FileName"] = f"{file_name}.mvr"
                commit_template["Comment"] = commit.comment
                commits.append(commit_template)
            data.outb.append(
                mvrx_message.craft_packet(
                    mvrx_message.create_message(
                        "MVR_JOIN_RET", commits=commits, uuid=self.uuid
                    )
                )
            )
            # data.outb.append(mvr_message.create_message("MVR_JOIN_RET"))
        if json_data["Type"] == "MVR_LEAVE":
            data.outb.append(
                mvrx_message.craft_packet(
                    mvrx_message.create_message("MVR_LEAVE_RET", uuid=self.uuid)
                )
            )
        if json_data["Type"] == "MVR_COMMIT":
            data.outb.append(
                mvrx_message.craft_packet(
                    mvrx_message.create_message("MVR_COMMIT_RET", uuid=self.uuid)
                )
            )
        if json_data["Type"] == "MVR_REQUEST":
            dmx = bpy.context.scene.dmx
            local_path = dmx.get_addon_path()
            file_uuid = json_data["FileUUID"]
            if not file_uuid:
                shared_commits = (
                    bpy.context.window_manager.dmx.mvr_xchange.shared_commits
                )
                if len(shared_commits):
                    last_commit = shared_commits[-1]
                    file_uuid = last_commit.commit_uuid
                    DMX_Log.log.debug("Sharing last version")

            ADDON_PATH = dmx.get_addon_path()
            file_path = os.path.join(
                ADDON_PATH, "assets", "mvrs", f"{file_uuid.upper()}.mvr"
            )

            DMX_Log.log.debug("sending file")
            if not os.path.exists(file_path):
                DMX_Log.log.error("MVR file for sending via MVR-xchange does not exist")

            file_size = os.path.getsize(file_path)
            file_object = open(file_path, "br")
            buffer = file_object.read(1024)
            data.outb.append(mvrx_message.craft_packet(None, file_size, buffer, 1))
            buffer = file_object.read(1024)
            while buffer:
                data.outb.append(buffer)
                buffer = file_object.read(1024)
            file_object.close()

        self.callback(json_data, data)

    def run(self):
        data_to_send = None
        while self.running:
            events = self.sel.select(timeout=1)
            if not self.post_data.empty():
                data_to_send = self.post_data.get()
            for key, mask in events:
                if key.data is None:
                    self.accept_wrapper(key.fileobj)
                else:
                    if data_to_send is not None:
                        key.data.outb.append(data_to_send)
                    self.service_connection(key, mask)
            data_to_send = None
        # self.sel.close()
