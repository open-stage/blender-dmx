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
import socket
import struct
import time
import socket

defined_provider_name = "BlenderDMX"
defined_station_name = (
    f"{defined_provider_name} station {socket.gethostname()}".replace(" ", "_")
)


class mvrx_message:
    @staticmethod
    def parse_header(data):
        header = {"Error": True}

        if len(data) >= 28:  # Ensure we have enough bytes for the full header
            magic = struct.unpack("!I", data[0:4])[0]
            if magic == 778682:
                # Unpack version, number, count, type, length
                msg_version, msg_number, msg_count, msg_type, msg_len = struct.unpack(
                    "!IIIIQ", data[4:28]
                )
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

        # Pack entire header in one call (5x uint32 + 1x uint64)
        header = struct.pack(
            "!IIIIIQ",
            MVR_PACKAGE_HEADER,
            MVR_PACKAGE_VERSION,
            MVR_PACKAGE_NUMBER,
            MVR_PACKAGE_COUNT,
            MVR_PACKAGE_TYPE,
            MVR_PAYLOAD_LENGTH,
        )

        return header + MVR_PAYLOAD_BUFFER

    join_message_ret = {
        "Commits": [],
        "Message": "",
        "OK": True,
        "Provider": defined_provider_name,
        "StationName": defined_station_name,
        "StationUUID": "",
        "Type": "MVR_JOIN_RET",
        "verMajor": 1,
        "verMinor": 6,
    }

    leave_message_ret = {"Type": "MVR_LEAVE_RET", "OK": True, "Message": ""}

    commit_message_ret = {"Type": "MVR_COMMIT_RET", "OK": True, "Message": ""}

    request_message = {
        "Type": "MVR_REQUEST",
        "FileUUID": "",
        "StationUUID": "",
        "FromStationUUID": [],
        "FromStationsUUID": [],
    }

    request_message_ret = {"Type": "MVR_REQUEST_RET", "OK": False, "Message": ""}

    join_message = {
        "Type": "MVR_JOIN",
        "Provider": defined_provider_name,
        "verMajor": 1,
        "verMinor": 6,
        "StationUUID": "",
        "StationName": defined_provider_name,
        "Commits": [],
    }

    leave_message = {
        "Type": "MVR_LEAVE",
        "StationUUID": "",
        "FromStationUUID": "",
    }

    commit_message = {
        "Type": "MVR_COMMIT",
        "verMajor": 1,
        "verMinor": 6,
        "FileSize": 0,
        "FileUUID": "",
        "StationUUID": "",
        "ForStationsUUID": [],
        "Comment": "Comment",
        "FileName": "",
    }

    @staticmethod
    def create_message(
        message,
        commits=None,
        uuid=None,
        file_uuid=None,
        ok=None,
        nok_reason=None,
        app_uuid=None,
    ):
        if message == "MVR_JOIN_RET":
            response = mvrx_message.join_message_ret.copy()
            response["StationName"] = f"{defined_station_name}"
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
            response["FileName"] = f"{commit.file_name}.mvr"
            response["StationUUID"] = uuid
            return response
        elif message == "MVR_COMMIT_RET":
            return mvrx_message.commit_message_ret.copy()
        elif message == "MVR_REQUEST":
            response = mvrx_message.request_message.copy()
            response["FileUUID"] = file_uuid
            response["StationUUID"] = app_uuid
            response[
                "FromStationUUID"
            ] = []  # the response seems to stay in memory, reset it
            response["FromStationUUID"].append(uuid)
            response[
                "FromStationsUUID"
            ] = []  # the response seems to stay in memory, reset it
            response["FromStationsUUID"].append(uuid)
            return response
        elif message == "MVR_JOIN":
            response = mvrx_message.join_message.copy()
            response["StationName"] = f"{defined_station_name}"
            response["StationUUID"] = uuid
            if commits is not None:
                response["Commits"] = commits
            return response
        elif message == "MVR_LEAVE":
            response = mvrx_message.leave_message.copy()
            response["StationUUID"] = uuid
            response["FromStationUUID"] = uuid
            return response
        elif message == "MVR_REQUEST_RET":
            response = mvrx_message.request_message_ret.copy()
            if ok is not None:
                response["OK"] = ok
            if nok_reason is not None:
                response["Message"] = nok_reason
            return response
