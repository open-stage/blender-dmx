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

import os
import socket
import selectors
import types
import json
import bpy
import time
from threading import Thread
from uuid import uuid4
from datetime import datetime
from ...mvrxchange.mvr_message import mvr_message
from ...logging import DMX_Log


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
        self.post_data = []

    def stop(self):
        self.running = False
        if self.lsock is not None:
            self.sel.close()
            self.lsock.close()
        self.join()

    def set_post_data(self, commit):
        DMX_Log.log.debug(f"Setting post data")
        commits = [commit]
        self.post_data.append(mvr_message.craft_packet(mvr_message.create_message("MVR_COMMIT", commits=commits, uuid=self.uuid)))

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
            dmx = bpy.context.scene.dmx
            local_path = dmx.get_addon_path()
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
        if json_data["Type"] == "MVR_JOIN":
            shared_commits = bpy.context.window_manager.dmx.mvr_xchange.shared_commits
            commits = []
            for commit in shared_commits:
                commit_template = mvr_message.commit_message.copy()
                commit_template["FileSize"] = commit.file_size
                commit_template["FileUUID"] = commit.commit_uuid
                commit_template["StationUUID"] = self.uuid
                commit_template["FileName"] = commit.file_name or commit.comment.replace(" ", "_")
                commit_template["Comment"] = commit.comment
                commits.append(commit_template)
            data.outb.append(mvr_message.craft_packet(mvr_message.create_message("MVR_JOIN_RET", commits=commits, uuid=self.uuid)))
            # data.outb.append(mvr_message.create_message("MVR_JOIN_RET"))
        if json_data["Type"] == "MVR_LEAVE":
            data.outb.append(mvr_message.craft_packet(mvr_message.create_message("MVR_LEAVE_RET", uuid=self.uuid)))
        if json_data["Type"] == "MVR_COMMIT":
            data.outb.append(mvr_message.craft_packet(mvr_message.create_message("MVR_COMMIT_RET", uuid=self.uuid)))
        if json_data["Type"] == "MVR_REQUEST":
            dmx = bpy.context.scene.dmx
            local_path = dmx.get_addon_path()
            file_uuid = json_data["FileUUID"]
            if not file_uuid:
                shared_commits = bpy.context.window_manager.dmx.mvr_xchange.shared_commits
                if len(shared_commits):
                    last_commit = shared_commits[-1]
                    file_uuid = last_commit.commit_uuid
                    DMX_Log.log.debug("Sharing last version")

            ADDON_PATH = dmx.get_addon_path()
            file_path = os.path.join(ADDON_PATH, "assets", "mvrs", f"{file_uuid}.mvr")

            DMX_Log.log.debug("sending file")
            if not os.path.exists(file_path):
                DMX_Log.log.error("MVR file for sending via MVR-xchange does not exist")

            file_size = os.path.getsize(file_path)
            file_object = open(file_path, "br")
            buffer = file_object.read(1024)
            data.outb.append(mvr_message.craft_packet(None, file_size, buffer, 1))
            buffer = file_object.read(1024)
            while buffer:
                data.outb.append(buffer)
                buffer = file_object.read(1024)
            file_object.close()

        self.callback(json_data, data)

    def run(self):
        post_data = None
        while self.running:
            events = self.sel.select(timeout=1)
            if self.post_data:
                post_data = self.post_data.pop(0)
            for key, mask in events:
                if key.data is None:
                    self.accept_wrapper(key.fileobj)
                else:
                    if post_data is not None:
                        key.data.outb.append(post_data)
                    self.service_connection(key, mask)
            post_data = None
        # self.sel.close()


if __name__ == "__main__":
    serve = server()
    serve.start()
