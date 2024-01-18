import json
import struct


class mvr_message:
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
        "Provider": "Blender DMX",
        "StationName": "Blender DMX Station",
        "StationUUID": "",
        "Type": "MVR_JOIN_RET",
        "verMajor": 1,
        "verMinor": 6,
    }

    leave_message_ret = {"Type": "MVR_LEAVE_RET", "OK": "true"}

    commit_message_ret = {"Type": "MVR_COMMIT_RET", "OK": "true"}

    request_message = {
        "Type": "MVR_REQUEST",
        "FileUUID": "",
        "FromStationUUID": "",
    }

    join_message = {
        "Type": "MVR_JOIN",
        "Provider": "Blender DMX",
        "verMajor": 1,
        "verMinor": 6,
        "StationUUID": "",
        "StationName": "Blender DMX Station",
        "Commits": [],
    }
    leave_message = {
        "Type": "MVR_LEAVE",
        "FromStationUUID": "",
    }

    request_message = {
        "Type": "MVR_REQUEST",
        "FileUUID": "",
        "FromStationUUID": "",
    }

    @staticmethod
    def create_message(message, files=[], uuid=None, file_uuid=None, ok=None, nok_reason=None):
        if message == "MVR_JOIN_RET":
            response = mvr_message.join_message_ret
            response["StationUUID"] = uuid
            if len(files) > 0:
                response["Commits"] = files
            if ok is not None:
                response["OK"] = ok
            if nok_reason is not None:
                response["Message"] = nok_reason
            return mvr_message.craft_packet(response)
        elif message == "MVR_LEAVE_RET":
            return mvr_message.craft_packet(mvr_message.leave_message_ret)
        elif message == "MVR_COMMIT_RET":
            return mvr_message.craft_packet(mvr_message.commit_message_ret)
        elif message == "MVR_REQUEST":
            response = mvr_message.request_message
            response["FileUUID"] = file_uuid
            response["FromStationUUID"] = uuid
            return mvr_message.craft_packet(response)
        elif message == "MVR_JOIN":
            response = mvr_message.join_message
            response["StationUUID"] = uuid
            if len(files) > 0:
                response["Commits"] = files
            return mvr_message.craft_packet(response)
        elif message == "MVR_LEAVE":
            response = mvr_message.leave_message
            response["FromStationUUID"] = uuid
            return mvr_message.craft_packet(response)
        elif message == "MVR_REQUEST":
            response = mvr_message.request_message
            response["StationUUID"] = uuid
            return mvr_message.craft_packet(response)
