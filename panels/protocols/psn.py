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

import bpy
from bpy.props import StringProperty, IntProperty
from bpy.types import Operator, Panel, UIList
from ...tracker import DMX_Tracker

from ...i18n import DMX_Lang

_ = DMX_Lang._


class DMX_OP_DMX_Tracker_Add(Operator):
    bl_label = _("Add Tracker")
    bl_description = _("Adding a tracker")
    bl_idname = "dmx.dmx_add_tracker"
    bl_options = {"UNDO"}

    def execute(self, context):
        DMX_Tracker.add_tracker()
        return {"FINISHED"}


class DMX_OP_DMX_Tracker_Remove(Operator):
    bl_label = _("Remove Tracker")
    bl_description = _("Removing a tracker")
    bl_idname = "dmx.dmx_remove_tracker"
    bl_options = {"UNDO"}

    uuid: StringProperty()

    def execute(self, context):
        DMX_Tracker.remove_tracker(self.uuid)
        return {"FINISHED"}


class DMX_UL_Tracker(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        icon = "FILE_VOLUME"
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            col = layout.column()
            col.ui_units_x = 3
            col = layout.column()
            col.prop(item, "name", text="", emboss=False)
            col = layout.column()
            col.prop(item, "enabled", text="")
            col = layout.column()
            col.operator("dmx.dmx_remove_tracker", text="", icon="TRASH").uuid = item.uuid
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text=str(item.id), icon=icon)


class DMX_OP_Link_Fixture_Tracker(Operator):
    bl_label = _("Link Fixture to Tracker")
    bl_description = _("Link fixture to a tracker")
    bl_idname = "dmx.psn_tracker_follower_link"
    bl_options = {"UNDO"}

    fixture_uuid: StringProperty()
    tracker_uuid: StringProperty()
    tracker_index: IntProperty()

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        dmx = scene.dmx
        layout = self.layout
        target = None
        for tracker in dmx.trackers:
            if tracker.uuid == self.tracker_uuid:
                for idx, obj in enumerate(tracker.collection.objects):
                    if idx == self.tracker_index:
                        target = obj

        if target is not None:
            for fixture in dmx.fixtures:
                if fixture.uuid == self.fixture_uuid:
                    for obj in fixture.objects:
                        if obj.name == "Target":
                            constraint = obj.object.constraints.new(type="COPY_LOCATION")
                            constraint.target = target

        return {"FINISHED"}


class DMX_OP_Unlink_Fixture_Tracker(Operator):
    bl_label = _("Unlink Fixture from Tracker")
    bl_description = _("Unlink fixture from a tracker")
    bl_idname = "dmx.psn_tracker_follower_unlink"
    bl_options = {"UNDO"}

    fixture_uuid: StringProperty()
    tracker_uuid: StringProperty()

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        layout = self.layout
        for fixture in dmx.fixtures:
            if fixture.uuid == self.fixture_uuid:
                for obj in fixture.objects:
                    if obj.name == "Target":
                        for constraint in obj.object.constraints:
                            if constraint.target is not None:
                                if constraint.target.get("uuid", None) == self.tracker_uuid:
                                    obj.object.constraints.remove(constraint)

        return {"FINISHED"}


class DMX_UL_Tracker_Followers(UIList):
    tracker_uuid: StringProperty()
    tracker_index: IntProperty()

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        fixture = item
        scene = context.scene
        dmx = scene.dmx
        icon = "FILE_VOLUME"
        self.tracker_uuid = context.window_manager.dmx.selected_tracker
        self.tracker_index = context.window_manager.dmx.selected_tracker_index

        linked = None
        for obj in fixture.objects:
            if obj.name == "Target":
                linked = False
                for const in obj.object.constraints:
                    if const.target is not None:
                        if const.target.get("uuid", None) == self.tracker_uuid:
                            linked = True

        if self.layout_type in {"DEFAULT", "COMPACT"}:
            col = layout.column()
            col.ui_units_x = 3
            col = layout.column()
            col.prop(item, "name", text="", emboss=False)
            col = layout.column()
            if linked is None:
                layout.label(text="", icon="CANCEL")
            elif linked is True:
                op = col.operator("dmx.psn_tracker_follower_unlink", icon="LINKED", text="")
                op.fixture_uuid = fixture.uuid
                op.tracker_uuid = self.tracker_uuid
            else:
                op = col.operator("dmx.psn_tracker_follower_link", icon="UNLINKED", text="")
                op.fixture_uuid = fixture.uuid
                op.tracker_uuid = self.tracker_uuid
                op.tracker_index = self.tracker_index
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text=item.name, icon=icon)


class DMX_OT_Tracker_Followers(Operator):
    bl_label = _("Tracker Followers")
    bl_idname = "dmx.psn_tracker_followers"
    bl_description = _("Link followers to a tracker")
    bl_options = {"UNDO"}

    tracker_uuid: StringProperty()
    tracker_index: IntProperty()
    fixture_i: IntProperty()

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx
        context.window_manager.dmx.selected_tracker = self.tracker_uuid
        context.window_manager.dmx.selected_tracker_index = self.tracker_index
        layout.template_list("DMX_UL_Tracker_Followers", "", dmx, "fixtures", self, "fixture_i")

    def execute(self, context):
        return {"FINISHED"}
        return {"CANCELLED"}

    def invoke(self, context, event):
        # self.name = "Group " + str(len(context.scene.dmx.groups)+1)
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class DMX_PT_DMX_Trackers(Panel):
    bl_label = _("PSN")
    bl_idname = "DMX_PT_DMX_Trackers"
    bl_parent_id = "DMX_PT_DMX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx
        layout.operator("dmx.dmx_add_tracker", text="Add tracker", icon="PLUS")
        layout.template_list("DMX_UL_Tracker", "", dmx, "trackers", dmx, "trackers_i")

        if dmx.trackers_i < len(dmx.trackers):
            tracker = dmx.trackers[dmx.trackers_i]
            layout.prop(tracker, "name")
            layout.prop(tracker, "ip_address")
            layout.prop(tracker, "ip_port")
            layout.prop(tracker, "enabled")
            add_trackers = True
            for idx, obj in enumerate(tracker.collection.objects):
                row = layout.row()
                col = row.column()
                op = col.operator("dmx.psn_tracker_followers", text=_(f"Link Followers to {obj.name}"), icon="LINKED")
                op.tracker_uuid = tracker.uuid
                op.tracker_index = idx
                if len(tracker.collection.objects) > 1:
                    col = row.column()
                    op = col.operator("dmx.psn_remove_tracker_followers_target", text="", icon="TRASH")
                    op.object_name = obj.name
                    op.tracker_uuid = tracker.uuid

                if idx >= 9:  # we support max 10 trackers, edit tracker.py and psn.py if more is needed
                    add_trackers = False
            row = layout.row()
            op = row.operator("dmx.psn_add_tracker_followers_target", text=_("Add Tracking Target"), icon="PLUS")
            op.tracker_uuid = tracker.uuid
            row.enabled = add_trackers


class DMX_OT_Tracker_Followers_Remove_Target(Operator):
    bl_label = _("Remove Followers Target")
    bl_idname = "dmx.psn_remove_tracker_followers_target"
    bl_description = _("Remove target")
    bl_options = {"UNDO"}

    object_name: StringProperty()
    tracker_uuid: StringProperty()

    def execute(self, context):
        dmx = context.scene.dmx
        for tracker in dmx.trackers:
            if tracker.uuid == self.tracker_uuid:
                if self.object_name in tracker.collection.objects:
                    rem_obj = tracker.collection.objects[self.object_name]
                    bpy.data.objects.remove(rem_obj)

        return {"FINISHED"}


class DMX_OT_Tracker_Followers_Add_Target(Operator):
    bl_label = _("Add Followers Target")
    bl_idname = "dmx.psn_add_tracker_followers_target"
    bl_description = _("Add target")
    bl_options = {"UNDO"}

    tracker_uuid: StringProperty()

    def execute(self, context):
        dmx = context.scene.dmx
        for tracker in dmx.trackers:
            if tracker.uuid == self.tracker_uuid:
                for obj in tracker.collection.objects:
                    duplicate_obj = obj.copy()
                    tracker.collection.objects.link(duplicate_obj)
                    break

        return {"FINISHED"}
