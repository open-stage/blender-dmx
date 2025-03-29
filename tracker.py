# Copyright (C) 2024 vanous
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

import uuid

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import Collection, Object, PropertyGroup

from .i18n import DMX_Lang
from .network import DMX_Network
from .psn import DMX_PSN

_ = DMX_Lang._


class DMX_Tracker_Object(PropertyGroup):
    object: PointerProperty(name="Tracker > Object", type=Object)


class DMX_Tracker(PropertyGroup):
    def onPsnEnable(self, context):
        if self.enabled:
            DMX_PSN.enable(self)
        else:
            DMX_PSN.disable(self)

    enabled: BoolProperty(
        name=_("Enable PSN Input"),
        description=_("Enables PosiStageNet input"),
        default=False,
        update=onPsnEnable,
    )

    ip_address: EnumProperty(
        name=_("IPv4 Address for PSN signal"),
        description=_("The network card/interface to listen for PSN data"),
        items=DMX_Network.cards,
    )

    ip_port: IntProperty(name=_("PSN Target port"), description=_(""), default=56565)

    uuid: StringProperty(
        name="UUID",
        description="Unique ID, used for identification",
        default=str(uuid.uuid4()),
    )
    # Blender RNA #

    collection: PointerProperty(name="Tracker > Collection", type=Collection)

    objects: CollectionProperty(name="Tracker > Objects", type=DMX_Tracker_Object)

    @staticmethod
    def add_tracker():
        dmx = bpy.context.scene.dmx
        new_tracker = dmx.trackers.add()
        new_tracker["position"] = [
            [],
        ] * 10  # hardcoded to 10 slots
        new_tracker.uuid = str(uuid.uuid4())
        new_id = len(dmx.trackers)
        new_tracker.name = generate_tracker_name(new_id)
        target = bpy.data.objects.new(
            name=f"{new_tracker.name} Tracker", object_data=None
        )
        target["uuid"] = new_tracker.uuid
        bpy.ops.collection.create(name=new_tracker.name)
        new_tracker.collection = bpy.data.collections[new_tracker.name]
        for c in new_tracker.collection.objects:
            new_tracker.collection.objects.unlink(c)
        for c in new_tracker.collection.children:
            new_tracker.collection.children.unlink(c)
        tracker_object = new_tracker.objects.add()
        new_tracker.collection.objects.link(target)
        tracker_object.name = new_tracker.name
        tracker_object.object = target
        target.empty_display_size = 0.2
        target.empty_display_type = "ARROWS"
        target.location = (0, 0, 0)
        bpy.context.scene.dmx.collection.children.link(new_tracker.collection)

    @staticmethod
    def remove_tracker(uuid):
        dmx = bpy.context.scene.dmx
        tracker_idx = DMX_Tracker.get_tracker_idx(uuid)
        tracker = DMX_Tracker.get_tracker(uuid)
        tracker.enabled = False
        for fixture in dmx.fixtures:
            for obj in fixture.objects:
                if obj.name == "Target":
                    for constraint in obj.object.constraints:
                        if constraint.target is not None:
                            if constraint.target.get("uuid", None) == uuid:
                                obj.object.constraints.remove(constraint)

        if tracker is not None:
            if tracker.collection is not None:
                if tracker.collection.objects is not None:
                    for obj in tracker.collection.objects:
                        bpy.data.objects.remove(obj)
            if tracker.objects is not None:
                for obj in tracker.objects:
                    if obj.object:
                        bpy.data.objects.remove(obj.object)
            if tracker.collection is not None:
                bpy.data.collections.remove(tracker.collection)
        if tracker_idx is not None:
            dmx.trackers.remove(tracker_idx)

    @staticmethod
    def get_tracker_idx(uuid):
        dmx = bpy.context.scene.dmx
        for idx, tracker in enumerate(dmx.trackers):
            if tracker.uuid == uuid:
                return idx

    @staticmethod
    def get_tracker(uuid):
        dmx = bpy.context.scene.dmx
        for tracker in dmx.trackers:
            if tracker.uuid == uuid:
                return tracker

    def render(self, current_frame=None):
        data = DMX_PSN.get_data(self.uuid)
        for idx, slot_data in enumerate(data):
            if idx > 10:  # hardcoded number of PSN slots
                return
            if list(self["position"][idx]) == list(slot_data):
                return

            x, y, z = slot_data
            self["position"][idx] = list(data)

            for obj_idx, obj in enumerate(self.collection.objects):
                if obj_idx == idx:
                    if x is not None:
                        obj.location.x = x
                    if y is not None:
                        obj.location.y = y
                    if z is not None:
                        obj.location.z = z
                    if current_frame:
                        obj.keyframe_insert(data_path="location", frame=current_frame)


def generate_tracker_name(new_id):
    dmx = bpy.context.scene.dmx
    while True:
        name = f"PSN Server {new_id:>03}"
        if name in dmx.trackers or name in dmx.collection.children:
            new_id += 1
        else:
            break
    return name
