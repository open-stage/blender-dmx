# Copyright (C) 2025 vanous
#
# This file is part of BlenderDMX.
#
# BlenderDMX is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# BlenderDMX is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.

import json
import logging
import threading
import time
from queue import Queue
import bpy
import websocket

from ..logging_setup import DMX_Log
from .mvrx_message import mvrx_message


class WebSocketClient(threading.Thread):
    """WebSocket Client that connects to a WebSocket server and allows sending and receiving messages."""

    def __init__(self, server_url, callback=None, application_uuid=0):
        super().__init__(name=f"WebSocketClient-{int(time.time())}")
        if DMX_Log.log.isEnabledFor(logging.DEBUG):
            websocket.enableTrace(True)
        self.server_url = server_url
        self.application_uuid = application_uuid
        self.callback = callback
        self.message_queue = Queue()
        self.running = True
        self.error = None
        self.commit = None
        self.filepath = None
        self.ws = None
        self.file_buffer = b""

    def run(self):
        """Run the client, connecting to the server and waiting for events."""
        while self.running:
            try:
                self.ws = websocket.WebSocketApp(
                    self.server_url,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close,
                )
                self.ws.on_open = self.on_open
                self.ws.run_forever(
                    reconnect=5,
                    ping_timeout=30,
                )
            except Exception as e:
                self.error = e
                DMX_Log.log.error(e)
                time.sleep(1)  # Delay before attempting to reconnect
                self.reconnect()

    def reconnect(self):
        DMX_Log.log.info("Reconnecting to the WebSocket server...")

    def on_message(self, ws, message):
        DMX_Log.log.debug(("Message received", len(message)))

        if isinstance(message, bytes):
            self.file_buffer += message
            if len(self.file_buffer) == self.commit.file_size:
                with open(self.filepath, "bw") as f:
                    f.write(self.file_buffer)
                self.file_buffer = b""
                self.callback(
                    {
                        "file_downloaded": self.commit,
                        "StationUUID": self.commit.station_uuid,
                    }
                )
        else:
            if self.callback:
                self.callback(json.loads(message))

    def on_error(self, ws, error):
        DMX_Log.log.error(("WebSocket error:", error))

    def on_close(self, ws, close_status_code, close_msg):
        DMX_Log.log.info(("Disconnected", close_status_code, close_msg))

    def on_open(self, ws):
        self.join_mvr()
        DMX_Log.log.info("Joining")

        # Start a thread to process the queue
        threading.Thread(target=self.process_queue, daemon=True).start()

    def send(self, message):
        """Add a message to the queue to be sent to the server."""

        if isinstance(message, bytes):
            self.message_queue.put(message)
        else:
            self.message_queue.put(json.dumps(message))
        # self.message_queue.put(json.dumps({"test": "message"}))
        DMX_Log.log.debug(("Message queued", len(message)))

    def process_queue(self):
        """Process the message queue and send messages to the server."""
        while self.running:
            try:
                message = self.message_queue.get(block=True, timeout=None)
                if isinstance(message, bytes):
                    self.ws.send(message, opcode=2)
                else:
                    self.ws.send(message)
                DMX_Log.log.debug(("Message sent", len(message)))
                self.message_queue.task_done()
                DMX_Log.log.debug("task done")
            except Exception as e:
                # Handle exceptions (e.g., timeout)
                DMX_Log.log.error(f"Error processing message queue: {e}")
                continue

    def stop(self):
        """Stop the client and clean up resources."""
        self.running = False
        self.ws.close()
        DMX_Log.log.debug("Client stopped.")
        self.join()  # not needed. close the thread

    def request_file(self, commit, path):
        self.filepath = path
        self.commit = commit
        commit_uuid = commit.commit_uuid
        self.send(
            mvrx_message.create_message(
                "MVR_REQUEST", uuid=commit.station_uuid, file_uuid=commit_uuid
            )
        )

    def join_mvr(self):
        shared_commits = bpy.context.window_manager.dmx.mvr_xchange.shared_commits
        commits = []
        for commit in shared_commits:
            commit_template = mvrx_message.commit_message.copy()
            commit_template["FileSize"] = commit.file_size
            commit_template["FileUUID"] = commit.commit_uuid
            commit_template["StationUUID"] = self.application_uuid
            file_name = commit.file_name or commit.comment.replace(" ", "_")
            commit_template["FileName"] = f"{file_name}.mvr"
            commit_template["Comment"] = commit.comment
            commits.append(commit_template)
        self.send(
            mvrx_message.create_message(
                "MVR_JOIN", commits=commits, uuid=self.application_uuid
            )
        )

    def send_commit(self, commit):
        commits = [commit]
        self.send(
            mvrx_message.create_message(
                "MVR_COMMIT", commits=commits, uuid=self.application_uuid
            )
        )

    def leave_mvr(self):
        self.send(mvrx_message.create_message("MVR_LEAVE", uuid=self.application_uuid))
