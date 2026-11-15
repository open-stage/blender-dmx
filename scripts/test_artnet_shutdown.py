# Copyright (C) 2026 Open Stage
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

# Run with: python3 scripts/test_artnet_shutdown.py

import importlib.util
from pathlib import Path
import socket
import struct
import sys
import threading
import time
import types
import unittest
from unittest.mock import Mock


class DMXDataStub:
    set_universe_hook = None

    @classmethod
    def set_universe(cls, *args):
        if cls.set_universe_hook:
            cls.set_universe_hook(*args)


def load_artnet(bpy):
    """Load artnet.py with small stand-ins for its Blender dependencies."""
    package_name = "_blender_dmx_artnet_test"
    module_names = [
        "bpy",
        package_name,
        f"{package_name}.data",
        f"{package_name}.logging_setup",
        f"{package_name}.network",
        f"{package_name}.artnet",
    ]
    previous_modules = {name: sys.modules.get(name) for name in module_names}

    package = types.ModuleType(package_name)
    package.__path__ = []
    data = types.ModuleType(f"{package_name}.data")
    data.DMX_Data = DMXDataStub
    logging_setup = types.ModuleType(f"{package_name}.logging_setup")
    logging_setup.DMX_Log = types.SimpleNamespace(log=Mock())
    network = types.ModuleType(f"{package_name}.network")
    network.DMX_Network = types.SimpleNamespace(cards=lambda *args: [])

    replacements = {
        "bpy": bpy,
        package_name: package,
        data.__name__: data,
        logging_setup.__name__: logging_setup,
        network.__name__: network,
    }

    try:
        sys.modules.update(replacements)
        module_name = f"{package_name}.artnet"
        spec = importlib.util.spec_from_file_location(
            module_name, Path(__file__).resolve().parents[1] / "artnet.py"
        )
        artnet = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = artnet
        spec.loader.exec_module(artnet)
        return artnet
    finally:
        for name, previous in previous_modules.items():
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous


bpy = types.ModuleType("bpy")
bpy.context = types.SimpleNamespace(scene=types.SimpleNamespace(dmx=None))
artnet = load_artnet(bpy)
artnet.ARTNET_PORT = 0


def art_dmx_packet(data=b"\x00\x01"):
    return b"".join(
        [
            artnet.ArtnetPacket.ARTNET_HEADER,
            struct.pack("<H", artnet.ArtnetPacket.opcode_ArtDMX),
            struct.pack(">HBBBBH", 14, 0, 0, 0, 0, len(data)),
            data,
        ]
    )


class TestArtNetShutdown(unittest.TestCase):
    def setUp(self):
        self.dmx = types.SimpleNamespace(
            artnet_ipaddr="127.0.0.1",
            artnet_status="offline",
            universes=[types.SimpleNamespace(input="ARTNET")],
        )
        bpy.context.scene.dmx = self.dmx
        artnet.DMX_ArtNet._thread = None
        DMXDataStub.set_universe_hook = None
        self.original_stop_check = artnet.STOP_CHECK_SECONDS
        # Keep the test fast. This also makes the old four-timeout join expire
        # after 40 ms, while the delayed packet handler is still blocked.
        artnet.STOP_CHECK_SECONDS = 0.01

    def tearDown(self):
        DMXDataStub.set_universe_hook = None
        receiver = artnet.DMX_ArtNet._thread
        if receiver:
            receiver.stop()
            receiver.join(timeout=1)
            if receiver.is_alive():
                receiver._socket.close()
                receiver.join(timeout=1)
        artnet.DMX_ArtNet._thread = None
        artnet.STOP_CHECK_SECONDS = self.original_stop_check

    def test_disable_waits_for_delayed_packet_handler(self):
        entered_handler = threading.Event()
        release_handler = threading.Event()

        def delayed_set_universe(*args):
            entered_handler.set()
            release_handler.wait(timeout=2)

        DMXDataStub.set_universe_hook = delayed_set_universe
        receiver = artnet.DMX_ArtNet("127.0.0.1")
        artnet.DMX_ArtNet._thread = receiver
        receiver.start()
        sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        disable_errors = []
        disabler = None

        def disable():
            try:
                artnet.DMX_ArtNet.disable()
            except Exception as error:
                disable_errors.append(error)

        try:
            sender.sendto(art_dmx_packet(), receiver._socket.getsockname())
            self.assertTrue(entered_handler.wait(timeout=1))

            disabler = threading.Thread(target=disable)
            disabler.start()
            deadline = time.monotonic() + 1
            while not receiver._stopped and time.monotonic() < deadline:
                time.sleep(0.001)
            self.assertTrue(receiver._stopped)

            # The receiver is still using Blender data. disable() must not
            # return, forget it, or report that the socket is offline yet.
            disabler.join(timeout=0.1)
            self.assertTrue(disabler.is_alive())
            self.assertIs(artnet.DMX_ArtNet._thread, receiver)
            self.assertEqual(self.dmx.artnet_status, "stop")

            release_handler.set()
            disabler.join(timeout=1)
            self.assertFalse(disabler.is_alive())
            self.assertEqual(disable_errors, [])
            self.assertFalse(receiver.is_alive())
            self.assertEqual(receiver._socket.fileno(), -1)
            self.assertIsNone(artnet.DMX_ArtNet._thread)
            self.assertEqual(self.dmx.artnet_status, "offline")
        finally:
            release_handler.set()
            sender.close()
            receiver.stop()
            if disabler:
                disabler.join(timeout=1)
            receiver.join(timeout=1)

    def test_repeated_enable_and_disable_leaves_no_receiver(self):
        for _ in range(3):
            artnet.DMX_ArtNet.enable()
            receiver = artnet.DMX_ArtNet._thread
            artnet.DMX_ArtNet.disable()
            self.assertFalse(receiver.is_alive())
            self.assertEqual(receiver._socket.fileno(), -1)
            self.assertIsNone(artnet.DMX_ArtNet._thread)
            self.assertEqual(self.dmx.artnet_status, "offline")

    def test_artpoll_is_not_handled_after_stop(self):
        receiver = artnet.DMX_ArtNet("127.0.0.1")
        try:
            receiver._socket.close()
            receiver._socket = Mock()
            receiver.build_ArtPollReply = Mock(return_value=b"reply")
            receiver.stop()
            receiver.handle_ArtPoll()
            receiver.build_ArtPollReply.assert_not_called()
            receiver._socket.sendto.assert_not_called()
        finally:
            receiver._socket.close()


if __name__ == "__main__":
    unittest.main()
