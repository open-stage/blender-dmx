import bpy
from bpy.types import Panel


from i18n import DMX_Lang
_ = DMX_Lang._

from src.icon import DMX_Icon

from .operator import ( DMX_OP_Programmer_SelectAll,
                        DMX_OP_Programmer_SelectInvert,
                        DMX_OP_Programmer_SelectEveryOther,
                        DMX_OP_Programmer_DeselectAll,
                        DMX_OP_Programmer_SelectBodies,
                        DMX_OP_Programmer_SelectTargets,
                        DMX_OP_Programmer_Clear )

class DMX_PT_Programmer(Panel):
    bl_label = _('Programmer')
    bl_idname = "DMX_PT_Programmer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        programmer = context.scene.dmx.programmer

        # layout.label(text='UGABUGA')

        row = layout.row()
        row.operator(
            DMX_OP_Programmer_SelectAll.bl_idname,
            text='', icon=DMX_Icon.SELECT_ALL
        )
        row.operator(
            DMX_OP_Programmer_SelectInvert.bl_idname,
            text='', icon=DMX_Icon.SELECT_INVERT
        )
        row.operator(
            DMX_OP_Programmer_SelectEveryOther.bl_idname,
            text='', icon=DMX_Icon.SELECT_EVERY_OTHER
        )
        row.operator(
            DMX_OP_Programmer_DeselectAll.bl_idname,
            text='', icon=DMX_Icon.DESELECT_ALL
        )

        row = layout.row()
        row.operator(
            DMX_OP_Programmer_SelectBodies.bl_idname
        )
        row.operator(
            DMX_OP_Programmer_SelectTargets.bl_idname
        )

        selected = len(bpy.context.selected_objects) > 0
        # if len(bpy.context.selected_objects) == 1:
        #     for fixture in dmx.fixtures:
        #         for obj in fixture.collection.objects:
        #             if (obj in bpy.context.selected_objects):
        #                 for obj in fixture.collection.objects:
        #                     if "MediaCamera" in obj.name:
        #                         row.operator("dmx.toggle_camera", text="Camera")
        # row.enabled = selected

        layout.template_color_picker(programmer,'color', value_slider=True)
        layout.prop(programmer,'dimmer', text='Dimmer')

        layout.prop(programmer, 'pan', text='Pan')
        layout.prop(programmer, 'tilt', text='Tilt')

        layout.prop(programmer, 'zoom', text='Zoom')
        layout.prop(programmer, 'shutter', text='Strobe')

        layout.operator(
            DMX_OP_Programmer_Clear.bl_idname,
            text='Clear' if selected else 'Clear All'
        )
