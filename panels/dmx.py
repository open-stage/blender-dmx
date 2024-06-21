#
#   BlendexDMX > Panels > DMX
#
#   - Setup DMX Universes
#   - Setup ArtNet (Future)
#
#   http://www.github.com/open-stage/BlenderDMX
#

import os

from bpy.props import StringProperty
from bpy.types import Menu, Operator, Panel, UIList
from ..mvrx_protocol import DMX_MVR_X_Client
from ..data import DMX_Data, IntProperty
from ..logging import DMX_Log
import uuid as py_uuid
from datetime import datetime
from ..tracker import DMX_Tracker

from ..i18n import DMX_Lang
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


class DMX_OP_MVR_Refresh(Operator):
    bl_label = _("Refresh")
    bl_description = _("Refresh connection")
    bl_idname = "dmx.mvr_refresh"
    bl_options = {"UNDO"}

    def execute(self, context):
        DMX_MVR_X_Client.re_join()
        return {"FINISHED"}


class DMX_OP_MVR_Request(Operator):
    bl_label = _("Request latest version")
    bl_description = _("Sends the Request message")
    bl_idname = "dmx.mvr_request"
    bl_options = {"UNDO"}

    station_uuid: StringProperty()

    def execute(self, context):
        uuid = str(py_uuid.uuid4())
        mvr_commit = {"FileUUID": uuid, "StationUUID": self.station_uuid,
                      "Comment": datetime.now().strftime("%H:%M:%S %B %d, %Y"), "FileSize": 0}

        last_commit = DMX_MVR_X_Client.create_self_request_commit(mvr_commit)
        if last_commit:
            DMX_MVR_X_Client.request_file(last_commit)

        return {"FINISHED"}

class DMX_OP_MVR_Import(Operator):
    bl_label = _("Import")
    bl_description = _("Import commit")
    bl_idname = "dmx.mvr_import"
    bl_options = {"UNDO"}

    uuid: StringProperty()

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
        clients = context.window_manager.dmx.mvr_xchange
        all_clients = context.window_manager.dmx.mvr_xchange.mvr_xchange_clients
        selected = clients.selected_mvr_client
        for client in all_clients:
            if client.station_uuid == selected:
                break
        for commit in client.commits:
            if commit.commit_uuid == self.uuid:
                DMX_Log.log.info(f"import {commit}")
                path = os.path.join(ADDON_PATH, "..", "assets", "mvrs", f"{commit.commit_uuid}.mvr")
                DMX_Log.log.info(path)
                dmx.addMVR(path)
                break
        return {"FINISHED"}

class DMX_OP_MVR_Download(Operator):
    bl_label = _("Download")
    bl_description = _("Download commit")
    bl_idname = "dmx.mvr_download"
    bl_options = {"UNDO"}

    uuid: StringProperty()

    def execute(self, context):
        DMX_Log.log.info("downloading")

        clients = context.window_manager.dmx.mvr_xchange
        all_clients = clients.mvr_xchange_clients
        selected = clients.selected_mvr_client
        for client in all_clients:
            if client.station_uuid == selected:
                break
        DMX_Log.log.info(f"got client {client.station_name}")
        for commit in client.commits:
            DMX_Log.log.info(commit.commit_uuid)
            if commit.commit_uuid == self.uuid:
                DMX_Log.log.info(f"downloading {commit}")
                DMX_MVR_X_Client.request_file(commit)
                break

        return {"FINISHED"}

class DMX_UL_MVR_Commit(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        scene = context.scene
        dmx = scene.dmx
        icon = "GROUP_VERTEX"
        #layout.context_pointer_set("mvr_xchange_clients", item)
        col = layout.column()
        col.label(text = f"{item.comment}", icon="CHECKBOX_HLT" if item.timestamp_saved else "CHECKBOX_DEHLT")
        col = layout.column()
        col.operator("dmx.mvr_download", text="", icon="IMPORT").uuid = item.commit_uuid
        col.enabled = dmx.mvrx_enabled
        col = layout.column()
        col.operator("dmx.mvr_import", text="", icon="CHECKBOX_HLT").uuid = item.commit_uuid
        col.enabled = item.timestamp_saved > 0


# List #

class DMX_UL_Tracker(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        icon = "FILE_VOLUME"
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            col = layout.column()
            col.ui_units_x = 3
            col = layout.column()
            col.prop(item, "name", text="", emboss=False)
            col = layout.column()
            col.prop(item, "enabled", text="")
            col = layout.column()
            col.operator("dmx.dmx_remove_tracker", text="", icon="TRASH").uuid = item.uuid
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text=str(item.id), icon=icon)

class DMX_UL_Universe(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        icon = "FILE_VOLUME"
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            col = layout.column()
            col.label(text=f"{item.id}", icon=icon)
            col.ui_units_x = 3
            col = layout.column()
            col.prop(item, "name", text="", emboss=False)
            col = layout.column()
            col.label(text=item.input)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text=str(item.id), icon=icon)



class DMX_OP_Link_Fixture_Tracker(Operator):
    bl_label = _("Link Fixture to Tracker")
    bl_description = _("Link fixture to a tracker")
    bl_idname = "dmx.psn_tracker_follower_link"
    bl_options = {"UNDO"}

    fixture_uuid: StringProperty()
    tracker_uuid: StringProperty()

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx

        dmx = scene.dmx
        layout = self.layout
        target = None
        for tracker in dmx.trackers:
            if tracker.uuid == self.tracker_uuid:
                for obj in tracker.objects:
                    target = obj.object


        for fixture in dmx.fixtures:
            if fixture.uuid == self.fixture_uuid:
                for obj in fixture.objects:
                    if obj.name == "Target":
                        constraint = obj.object.constraints.new(type='COPY_LOCATION')
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
        target = None
        for tracker in dmx.trackers:
            if tracker.uuid == self.tracker_uuid:
                for obj in tracker.objects:
                    target = obj.object

        for fixture in dmx.fixtures:
            if fixture.uuid == self.fixture_uuid:
                for obj in fixture.objects:
                    if obj.name == "Target":
                        for constraint in obj.object.constraints:
                            if constraint.target.get("uuid", None) == self.tracker_uuid:
                                obj.object.constraints.remove(constraint)


        return {"FINISHED"}



class DMX_UL_Tracker_Followers(UIList):

    tracker_uuid: StringProperty()

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        fixture = item
        scene = context.scene
        dmx = scene.dmx
        icon = "FILE_VOLUME"
        self.tracker_uuid = context.window_manager.dmx.selected_tracker

        linked = None
        for obj in fixture.objects:
            if obj.name == "Target":
                linked = False
                for const in obj.object.constraints:
                    if const.target is not None:
                        if const.target.get("uuid", None) == self.tracker_uuid:
                            linked = True

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
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
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text=item.name, icon=icon)


class DMX_OT_Tracker_Followers(Operator):
    bl_label = _("Tracker Followers")
    bl_idname = "dmx.psn_tracker_followers"
    bl_description = _("Link followers to a tracker")
    bl_options = {'UNDO'}

    tracker_uuid: StringProperty()
    fixture_i: IntProperty()

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx
        context.window_manager.dmx.selected_tracker = self.tracker_uuid
        layout.template_list("DMX_UL_Tracker_Followers", "", dmx, "fixtures", self, "fixture_i")


    def execute(self, context):
        return {'FINISHED'}
        return {'CANCELLED'}

    def invoke(self, context, event):
        #self.name = "Group " + str(len(context.scene.dmx.groups)+1)
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

# Menus #

class DMX_MT_Universe(Menu):
    bl_label = _("DMX > Universe Menu")
    bl_idname = "DMX_MT_Universe"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx

        # "Add"
        row = layout.row()
        #row.operator("dmx.add_universe", text="Add", icon="ADD")


# Sub-panels #
class DMX_PT_DMX_OSC(Panel):
    bl_label = _("OSC")
    bl_idname = "DMX_PT_DMX_OSC"
    bl_parent_id = "DMX_PT_DMX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx

        row = layout.row()
        row.prop(dmx, "osc_enabled")
        row = layout.row()
        row.prop(dmx, "osc_target_address")
        row.enabled = not dmx.osc_enabled
        row = layout.row()
        row.prop(dmx, "osc_target_port")
        row.enabled = not dmx.osc_enabled

class DMX_PT_DMX_Trackers(Panel):
    bl_label = _("PSN")
    bl_idname = "DMX_PT_DMX_Trackers"
    bl_parent_id = "DMX_PT_DMX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx
        layout.operator("dmx.dmx_add_tracker", text="Add tracker", icon="PLUS")
        layout.template_list("DMX_UL_Tracker", "", dmx, "trackers", dmx, "trackers_i")

        if (dmx.trackers_i < len(dmx.trackers)):
            tracker = dmx.trackers[dmx.trackers_i]
            layout.prop(tracker, "name")
            layout.prop(tracker, "ip_address")
            layout.prop(tracker, "ip_port")
            layout.prop(tracker, "enabled")
            layout.operator("dmx.psn_tracker_followers", text=_("Link Tracker Followers"), icon="PLUS").tracker_uuid = tracker.uuid

class DMX_PT_DMX_MVR_X(Panel):
    bl_label = _("MVR-xchange")
    bl_idname = "DMX_PT_DMX_MVR_Xchange"
    bl_parent_id = "DMX_PT_DMX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx

        row = layout.row()
        row.prop(dmx, "zeroconf_enabled")
        row = layout.row()

        clients = context.window_manager.dmx.mvr_xchange
        all_clients = clients.mvr_xchange_clients
        if not all_clients:
            selected = None
        else:
            selected = clients.selected_mvr_client

        client = None
        for client in all_clients:
            if client.station_uuid ==selected:
                break

        row.prop(clients, "selected_mvr_client", text="")
        row.enabled = not dmx.mvrx_enabled
        row = layout.row()
        col = row.column()
        row.prop(dmx, "mvrx_enabled")
        col1 = row.column()
        col1.operator("dmx.mvr_refresh", text="", icon="FILE_REFRESH")
        col2 = row.column()
        if client:
            col2.operator("dmx.mvr_request", text="", icon="IMPORT").station_uuid = client.station_uuid
        col1.enabled = col2.enabled = dmx.mvrx_enabled
        #row.operator("dmx.mvr_test", text="Test", icon="CANCEL")
        row.enabled = len(all_clients) > 0
        if not client:
            return
        row = layout.row()
        row.label(text = f"{client.station_name}", icon = "LINKED" if dmx.mvrx_enabled else "UNLINKED")
        layout.template_list(
            "DMX_UL_MVR_Commit",
            "",
            client,
            "commits",
            clients,
            "selected_commit",
            rows=4,
        )

class DMX_PT_DMX_Universes(Panel):
    bl_label = _("Universes")
    bl_idname = "DMX_PT_DMX_Universes"
    bl_parent_id = "DMX_PT_DMX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx

        layout.prop(dmx, "universes_n", text=_("Universes"))

        layout.template_list("DMX_UL_Universe", "", dmx, "universes", dmx, "universe_list_i")

        if (dmx.universe_list_i < dmx.universes_n):
            universe = dmx.universes[dmx.universe_list_i]
            layout.prop(universe, "name")
            layout.prop(universe, "input")

        #layout.menu("dmx.menu.universe", text="...", icon="FILE_VOLUME")

class DMX_PT_DMX_ArtNet(Panel):
    bl_label = _("Art-Net")
    bl_idname = "DMX_PT_DMX_ArtNet"
    bl_parent_id = "DMX_PT_DMX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx

        artnet_universes = []
        for universe in dmx.universes:
            if universe.input == "ARTNET":
                artnet_universes.append(universe)

        row = layout.row()
        row.prop(dmx, "artnet_ipaddr", text=_("IPv4"))
        row.enabled = not dmx.artnet_enabled

        row = layout.row()
        row.prop(dmx, "artnet_enabled")
        row.enabled = len(artnet_universes)>0
        row = layout.row()
        row.label(text=_("Art-Net set for {} universe(s)").format(len(artnet_universes)))
        layout.label(text=_("Status") + ": " + layout.enum_item_name(dmx, 'artnet_status', dmx.artnet_status))

class DMX_PT_DMX_sACN(Panel):
    bl_label = _("sACN")
    bl_idname = "DMX_PT_DMX_sACN"
    bl_parent_id = "DMX_PT_DMX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx

        sacn_universes = []
        for index, universe in enumerate(dmx.universes):
            if index == 0:  # invalid for sACN
                continue
            if universe.input == "sACN":
                sacn_universes.append(universe)

        row = layout.row()
        row.prop(dmx, "sacn_enabled")
        row.enabled = len(sacn_universes)>0
        row = layout.row()
        row.label(text=_("sACN set for {} universe(s)").format(len(sacn_universes)))
        layout.label(text=_("Status") + ": " + dmx.sacn_status)

class DMX_UL_LiveDMX_items(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.alignment = 'CENTER'
        layout.label(text=f"{index+1}: {DMX_Data._live_view_data[index]}")

    def invoke(self, context, event):
        pass

class DMX_PT_DMX_LiveDMX(Panel):
    bl_label = _("Live DMX")
    bl_idname = "DMX_PT_DMX_LiveDMX"
    bl_parent_id = "DMX_PT_DMX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}


    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx
        selected_universe = dmx.get_selected_live_dmx_universe()
        if selected_universe is None: # this should not happen
            raise ValueError("Missing selected universe, as if DMX base class is empty...")

        row = layout.row()
        row.prop(dmx, "selected_live_dmx", text=_("Source"))
        row = layout.row()
        col = row.column()
        col.label(text=f"{selected_universe.id}")
        col.ui_units_x = 2
        col = row.column()
        row.label(text=f"{selected_universe.name}")
        col = row.column()
        row.label(text=f"{selected_universe.input}")
        layout.template_list("DMX_UL_LiveDMX_items", "", dmx, "dmx_values", dmx, "dmx_value_index", type='GRID')

# Panel #

class DMX_PT_DMX(Panel):
    bl_label = _("Protocols")
    bl_idname = "DMX_PT_DMX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx
