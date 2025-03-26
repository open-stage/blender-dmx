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
import bpy.utils.previews
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import PropertyGroup

from . import fixture as fixture
from .fixture import DMX_Fixture_Channel
from .i18n import DMX_Lang
from .logging import DMX_Log
from .mvrxchange.mvr_xchange_blender import DMX_MVR_Xchange
from .panels import profiles as Profiles
from .panels import subfixtures

_ = DMX_Lang._


class DMX_TempData(PropertyGroup):
    filtered_subfixtures = []

    def set_filtered_subfixtures(self, subs):
        DMX_TempData.filtered_subfixtures = subs

    def onUpdateCollections(self, context):
        dmx = context.scene.dmx
        dmx.update_laser_collision_collect()

    def onToggleAddSelection(self, context):
        self.onChangingGroupSelectionBehavior("add")

    def onToggleSubSelection(self, context):
        self.onChangingGroupSelectionBehavior("sub")

    def onChangingGroupSelectionBehavior(self, behavior):
        if "add" in behavior:
            if self.aditive_selection:
                self.subtractive_selection = False
        else:  # sub
            if self.subtractive_selection:
                self.aditive_selection = False

    collections_list: PointerProperty(
        type=bpy.types.Collection,
        name=_("Laser collision collection"),
        description=_(
            "Laser beams are projected onto objects in this collection. The beam stops at the first object colliding with the beam."
        ),
        update=onUpdateCollections,
    )

    pause_render: BoolProperty(
        description="The renderer is paused during MVR import and in 2D view. This checkbox allows to re-enable it in case of some failure during import, which would leave it paused",
        name=_("Pause renderer"),
        default=False,
    )

    manufacturers: CollectionProperty(name=_("Manufacturers"), type=PropertyGroup)

    imports: PointerProperty(name=_("Imports"), type=Profiles.DMX_Fixtures_Imports)

    aditive_selection: BoolProperty(
        name=_("Add to selection"),
        description="When selecting a group, add to existing selection",
        update=onToggleAddSelection,
        default=True,
    )

    subtractive_selection: BoolProperty(
        name=_("Remove from selection"),
        description="When selecting a group, remove from existing selection",
        update=onToggleSubSelection,
        default=False,
    )

    keyframe_only_selected: BoolProperty(
        name=_("Keyframe only selected fixtures (not for autokeying)"),
        description="Add keyframes with changes only for selected fixtures",
        default=False,
    )

    mvr_xchange: PointerProperty(name=_("MVR-xchange"), type=DMX_MVR_Xchange)

    release_version_status: StringProperty(
        name=_("Status"),
        description="Information about latest release of BlenderDMX",
        default="Not checked",
    )

    def onUpdateLoggingFilter(self, context):
        DMX_Log.update_filters()

    logging_filter_mvr_xchange: BoolProperty(
        name=_("MVR-xchange"), default=False, update=onUpdateLoggingFilter
    )

    logging_filter_dmx_in: BoolProperty(
        name=_("DMX Data"), default=False, update=onUpdateLoggingFilter
    )

    logging_filter_fixture: BoolProperty(
        name=_("Fixture"), default=False, update=onUpdateLoggingFilter
    )

    selected_tracker: StringProperty()  # to pass data to fixture list
    selected_tracker_index: IntProperty()  # to pass data to fixture list

    dist_gap: FloatProperty(name="Gap", default=2)
    dist_diameter: FloatProperty(name="Diameter", default=2)
    dist_rotate: BoolProperty(name="Rotate", default=False)
    programmer_source: StringProperty(name="Source")

    subfixtures: CollectionProperty(
        name=_("Subfixtures"),
        type=subfixtures.DMX_Subfixture,
    )

    active_subfixtures: CollectionProperty(
        name=_("Active Subfixtures"), type=PropertyGroup
    )

    active_subfixture_i: IntProperty(default=-1)

    selected_fixture_label: StringProperty()

    migration_message: StringProperty()  # to pass data to fixture list

    pan_rotate_enabled: BoolProperty(name="Pan Rotate", default=False)
    tilt_rotate_enabled: BoolProperty(name="Tilt Rotate", default=False)
