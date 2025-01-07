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

import socketio
import threading
import time
import bpy
from queue import Queue
from ...mvrxchange.mvr_message import mvr_message
from ...logging import DMX_Log


class socket_client(threading.Thread):
    """Socket.IO Client that connects to a Socket.IO server and allows sending and receiving messages."""

    def __init__(self, server_url, callback=None, application_uuid=0):
        super().__init__(name=f"SocketIOClient-{int(time.time())}")
        self.server_url = server_url
        self.application_uuid = application_uuid
        self.callback = callback
        self.sio = socketio.Client()
        self.message_queue = Queue()
        self.running = True
        self.error = None
        self.commit = None
        self.filepath = None

        # Register the message event handler
        @self.sio.event
        def message(data):
            DMX_Log.log.debug(("Message received", len(data)))

            if isinstance(data, bytes):
                with open(self.filepath, "bw") as f:
                    f.write(data)
                self.callback({"file_downloaded": self.commit, "StationUUID": self.commit.station_uuid})
            else:
                if self.callback:
                    self.callback(data)

        @self.sio.event
        def connect():
            self.join_mvr()
            DMX_Log.log.info("Joining")

        @self.sio.event
        def disconnect():
            # this seems to be only received when we disconnect
            # not when the server disconnects us...
            DMX_Log.log.info("Disconnected")

    def run(self):
        """Run the client, connecting to the server and waiting for events."""
        try:
            self.sio.connect(self.server_url)
            DMX_Log.log.debug(f"Connected to server: {self.server_url}")
            threading.Thread(target=self.process_queue, daemon=True).start()  # Start a thread to process the queue
            self.sio.wait()  # Keep the thread alive to listen for events
        except Exception as e:
            self.error = e
            DMX_Log.log.error(e)

    def send(self, message):
        """Add a message to the queue to be sent to the server."""
        self.message_queue.put(message)
        DMX_Log.log.debug(("Message queued", len(message)))

    def process_queue(self):
        """Process the message queue and send messages to the server."""
        while self.running:
            try:
                message = self.message_queue.get(timeout=1)  # Wait for a message to be available
                self.sio.send(message)
                DMX_Log.log.debug(("Message sent", len(message)))
                self.message_queue.task_done()
                DMX_Log.log.debug("task done")
            except Exception as e:
                # this produces exceptions when message_queue is empty
                continue  # Handle exceptions (e.g., timeout)

    def stop(self):
        """Stop the client and clean up resources."""
        self.running = False
        self.sio.disconnect()
        DMX_Log.log.debug("Client stopped.")
        self.join()  # not needed. close the thread

    def request_file(self, commit, path):
        self.filepath = path
        self.commit = commit
        # if commit.self_requested:  # we need to provide empty UUID in this case
        #    commit_uuid = ""
        # else:
        #    commit_uuid = commit.commit_uuid
        commit_uuid = commit.commit_uuid
        self.send(mvr_message.create_message("MVR_REQUEST", uuid=commit.station_uuid, file_uuid=commit_uuid))

    def join_mvr(self):
        shared_commits = bpy.context.window_manager.dmx.mvr_xchange.shared_commits
        commits = []
        for commit in shared_commits:
            commit_template = mvr_message.commit_message.copy()
            commit_template["FileSize"] = commit.file_size
            commit_template["FileUUID"] = commit.commit_uuid
            commit_template["StationUUID"] = self.application_uuid
            commit_template["FileName"] = commit.file_name or commit.comment.replace(" ", "_")
            commit_template["Comment"] = commit.comment
            commits.append(commit_template)
        self.send(mvr_message.create_message("MVR_JOIN", commits=commits, uuid=self.application_uuid))

    def set_post_data(self, commit):
        commits = [commit]
        self.send(mvr_message.create_message("MVR_COMMIT", commits=commits, uuid=self.application_uuid))

    def leave_mvr(self):
        self.send(mvr_message.create_message("MVR_LEAVE", uuid=self.application_uuid))
