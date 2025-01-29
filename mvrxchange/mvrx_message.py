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
import socket
import struct

# mvr message structures


class mvrx_message:
    @staticmethod
    def parse_header(data):
        header = {"Error": True}
        if len(data) > 4:
            if struct.unpack("!l", data[0:4])[0] == 778682:
                msg_version = struct.unpack("!l", data[4:8])[0]
                msg_number = struct.unpack("!l", data[8:12])[0]
                msg_count = struct.unpack("!l", data[12:16])[0]
                msg_type = struct.unpack("!l", data[16:20])[0]
                msg_len = struct.unpack("!q", data[20:28])[0]
                header = {
                    "Version": msg_version,
                    "Number": msg_number,
                    "Count": msg_count,
                    "Type": msg_type,
                    "Data_len": msg_len,
                    "Total_len": msg_len + 28,
                    "Error": False,
                }
        return header

    @staticmethod
    def craft_packet(message=None, length=None, buffer=None, msg_type=0):
        MVR_PACKAGE_HEADER = 778682
        MVR_PACKAGE_VERSION = 1
        MVR_PACKAGE_NUMBER = 0
        MVR_PACKAGE_COUNT = 1
        MVR_PACKAGE_TYPE = msg_type
        MVR_PAYLOAD_BUFFER = buffer or json.dumps(message).encode("utf-8")
        MVR_PAYLOAD_LENGTH = length or len(MVR_PAYLOAD_BUFFER)

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

    join_message_ret = {
        "Commits": [],
        "Message": "",
        "OK": "true",
        "Provider": "BlenderDMX",
        "StationName": "BlenderDMX Station",
        "StationUUID": "",
        "Type": "MVR_JOIN_RET",
        "verMajor": 1,
        "verMinor": 6,
    }

    leave_message_ret = {"Type": "MVR_LEAVE_RET", "OK": "true", "Message": ""}

    commit_message_ret = {"Type": "MVR_COMMIT_RET", "OK": "true", "Message": ""}

    request_message = {
        "Type": "MVR_REQUEST",
        "FileUUID": "",
        "FromStationUUID": "",
    }

    join_message = {
        "Type": "MVR_JOIN",
        "Provider": "BlenderDMX",
        "verMajor": 1,
        "verMinor": 6,
        "StationUUID": "",
        "StationName": "BlenderDMX Station",
        "Commits": [],
    }

    leave_message = {
        "Type": "MVR_LEAVE",
        "FromStationUUID": "",
    }

    commit_message = {
        "Type": "MVR_COMMIT",
        "verMajor": 1,
        "verMinor": 6,
        "FileSize": "",
        "FileUUID": "",
        "StationUUID": "",
        "ForStationsUUID": [],
        "Comment": "Comment",
        "FileName": "",
    }

    @staticmethod
    def create_message(
        message, commits=None, uuid=None, file_uuid=None, ok=None, nok_reason=None
    ):
        if message == "MVR_JOIN_RET":
            response = mvrx_message.join_message_ret.copy()
            response["StationName"] = (
                f"BlenderDMX station {socket.gethostname()}".replace(" ", "_")
            )
            response["StationUUID"] = uuid
            if commits is not None:
                response["Commits"] = commits
            if ok is not None:
                response["OK"] = ok
            if nok_reason is not None:
                response["Message"] = nok_reason
            return response
        elif message == "MVR_LEAVE_RET":
            return mvrx_message.leave_message_ret.copy()
        elif message == "MVR_COMMIT":
            if commits is not None:
                commit = commits[-1]

            response = mvrx_message.commit_message.copy()
            response["FileSize"] = commit.file_size
            response["FileUUID"] = commit.commit_uuid
            response["Comment"] = commit.comment
            response["FileName"] = commit.file_name
            response["StationUUID"] = uuid
            return response
        elif message == "MVR_COMMIT_RET":
            return mvrx_message.commit_message_ret.copy()
        elif message == "MVR_REQUEST":
            response = mvrx_message.request_message.copy()
            response["FileUUID"] = file_uuid
            response["FromStationUUID"] = uuid
            return response
        elif message == "MVR_JOIN":
            response = mvrx_message.join_message.copy()
            response["StationName"] = f"BlenderDMX station {socket.gethostname()}"
            response["StationUUID"] = uuid
            if commits is not None:
                response["Commits"] = commits
            return response
        elif message == "MVR_LEAVE":
            response = mvrx_message.leave_message.copy()
            response["FromStationUUID"] = uuid
            return response
