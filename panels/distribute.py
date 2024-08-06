import bpy
import math

from bpy.props import FloatProperty, StringProperty
from bpy.types import (
    Operator,
    Panel,
)


from ..logging import DMX_Log

from ..i18n import DMX_Lang

_ = DMX_Lang._


class DMX_OP_AlignLocationOperator(Operator):
    bl_idname = "dmx.align_location"
    bl_label = "Align selected fixtures to active fixture"
    bl_description = "Align selected fixtures to active fixture"
    bl_options = {"UNDO"}

    axis: StringProperty(name="axis")

    def execute(self, context):
        axis = {"x": 0, "y": 1, "z": 2}[self.axis]

        active_object = bpy.context.active_object
        if active_object is None:
            return {"FINISHED"}

        dmx = context.scene.dmx
        selected_fixtures_objects = []
        for fixture in dmx.fixtures:
            for obj in fixture.collection.objects:
                if obj in bpy.context.selected_objects:
                    if obj == bpy.context.active_object:
                        continue
                    selected_fixtures_objects.append(obj)

        activeObjectAxisValue = active_object.location[axis]

        for o in selected_fixtures_objects:
            o.location[axis] = activeObjectAxisValue

        return {"FINISHED"}


# Distribute Evenly Operator


class DMX_OP_DistributeEvenlyOperator(Operator):
    bl_idname = "dmx.distribute_evenly"
    bl_label = "Distribute selected fixtures evenly"
    bl_description = "Distribute selected fixtures evenly"
    bl_options = {"UNDO"}

    axis: StringProperty(name="axis")

    def execute(self, context):
        axis = {"x": 0, "y": 1, "z": 2}[self.axis]

        active_object = bpy.context.active_object
        if active_object is None:
            return {"FINISHED"}
        dmx = context.scene.dmx
        selected_fixtures_objects = []
        for fixture in dmx.fixtures:
            for obj in fixture.collection.objects:
                if obj in bpy.context.selected_objects:
                    if obj == bpy.context.active_object:
                        continue
                    selected_fixtures_objects.append(obj)

        selected_fixtures_objects.sort(key=lambda o: o.location[axis])

        firstObjAxisValue = active_object.location[axis]

        def minMaxLambda(o):
            return o.location[axis]

        maxValue = max(selected_fixtures_objects, key=minMaxLambda).location[axis]
        minValue = min(selected_fixtures_objects, key=minMaxLambda).location[axis]

        length = maxValue - minValue
        spaceBetween = length / (len(selected_fixtures_objects) - 1)

        for i, o in enumerate(selected_fixtures_objects):
            o.location[axis] = firstObjAxisValue + (i * spaceBetween)

        return {"FINISHED"}


# Distribute With Gap Operator


class DMX_OP_DistributeWithGapOperator(Operator):
    bl_idname = "dmx.distribute_with_gap"
    bl_label = "Distribute selected fixtures with gap"
    bl_description = "Distribute selected fixtures with gap"
    bl_options = {"UNDO"}

    axis: StringProperty(name="axis")

    def execute(self, context):
        axis = {"x": 0, "y": 1, "z": 2}[self.axis]
        gap = bpy.context.window_manager.dmx.dist_gap
        active_object = bpy.context.active_object
        if active_object is None:
            return {"FINISHED"}

        dmx = context.scene.dmx
        selected_fixtures_objects = []
        for fixture in dmx.sortedFixtures():
            for obj in fixture.collection.objects:
                if obj in bpy.context.selected_objects:
                    if obj == bpy.context.active_object:
                        continue
                    selected_fixtures_objects.append(obj)

        if self.axis == "x":
            selected_fixtures_objects.sort(key=lambda o: o.location.y)
            selected_fixtures_objects.sort(key=lambda o: o.location.z)
        elif self.axis == "y":
            selected_fixtures_objects.sort(key=lambda o: o.location.x)
            selected_fixtures_objects.sort(key=lambda o: o.location.z)
        elif self.axis == "z":
            selected_fixtures_objects.sort(key=lambda o: o.location.y)
            selected_fixtures_objects.sort(key=lambda o: o.location.x)

        for i, o in enumerate(selected_fixtures_objects):
            o.location[axis] = active_object.location[axis] + ((i + 1) * gap)

        return {"FINISHED"}


class DMX_OP_DistributeCircle(Operator):
    bl_idname = "dmx.distribute_circle"
    bl_label = "Align selected fixtures to active fixture"
    bl_description = "Align selected fixtures to active fixture"
    bl_options = {"UNDO"}

    axis: StringProperty(name="axis")

    def points_on_circle(self, r, n=100):
        return [(math.cos(2 * math.pi / n * x) * r, math.sin(2 * math.pi / n * x) * r) for x in range(0, n + 1)]

    def execute(self, context):
        dmx = context.scene.dmx
        diameter = bpy.context.window_manager.dmx.dist_diameter
        rotate = bpy.context.window_manager.dmx.dist_rotate
        active_object = bpy.context.active_object
        if active_object is None:
            return {"FINISHED"}

        dmx = context.scene.dmx
        selected_fixtures_objects = []

        for fixture in dmx.sortedFixtures():
            for obj in fixture.collection.objects:
                if obj in bpy.context.selected_objects:
                    if obj == bpy.context.active_object:
                        continue
                    selected_fixtures_objects.append(obj)
        if not selected_fixtures_objects:
            return {"FINISHED"}

        points = self.points_on_circle(diameter, len(selected_fixtures_objects))

        rot = 360 / len(selected_fixtures_objects)

        for idx, o in enumerate(selected_fixtures_objects):
            if self.axis == "x":
                if rotate:
                    o.rotation_euler[0] += math.radians(rot * idx)
                o.location[1] = points[idx][0] + active_object.location[1]
                o.location[2] = points[idx][1] + active_object.location[2]
            if self.axis == "y":
                o.location[0] = points[idx][0] + active_object.location[0]
                if rotate:
                    o.rotation_euler[1] += math.radians(rot * idx)
                o.location[2] = points[idx][1] + active_object.location[2]
            if self.axis == "z":
                o.location[0] = points[idx][0] + active_object.location[0]
                o.location[1] = points[idx][1] + active_object.location[1]
                if rotate:
                    o.rotation_euler[2] += math.radians(rot * idx)

        return {"FINISHED"}


# Interface Panel


class DMX_PT_AlignAndDistributePanel(Panel):
    bl_label = _("Align and Distribute")
    bl_idname = "DMX_PT_AlignDistribute"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx
        selected_fixtures = []
        for fixture in dmx.fixtures:
            for obj in fixture.collection.objects:
                if obj in bpy.context.selected_objects:
                    selected_fixtures.append(fixture)

        active_object = bpy.context.active_object
        selected = len(selected_fixtures) > 0
        length_selected = len(selected_fixtures)
        active_name = "None"
        if active_object is not None:
            active_name = active_object.name

        stop = False
        for fixture in dmx.fixtures:
            if not stop:
                for obj in fixture.collection.objects:
                    if obj == active_object:
                        active_name = fixture.name
                        stop = True
                        break

        enable_this = (selected is True) and (active_object is not None)
        # align operators

        box = layout.column()
        col = box.column()
        col.label(text=_("Active object: {}".format(active_name)))
        col.label(text=_("Selected fixtures: {}".format(length_selected)))

        box = layout.column().box()
        box.enabled = enable_this
        col = box.column()
        col.label(text="Align")
        col = box.column_flow(columns=3, align=True)

        alignX = col.operator("dmx.align_location", text="X")
        alignX.axis = "x"

        alignY = col.operator("dmx.align_location", text="Y")
        alignY.axis = "y"

        alignZ = col.operator("dmx.align_location", text="Z")
        alignZ.axis = "z"

        # distribute evenly operators
        box = layout.column().box()

        box.enabled = enable_this and len(selected_fixtures) > 2
        col = box.column()
        col.label(text="Distribute evenly")
        col = box.column_flow(columns=3, align=True)

        distributeX = col.operator("dmx.distribute_evenly", text="X")
        distributeX.axis = "x"

        distributeY = col.operator("dmx.distribute_evenly", text="Y")
        distributeY.axis = "y"

        distributeZ = col.operator("dmx.distribute_evenly", text="Z")
        distributeZ.axis = "z"

        # distribute with gap operators
        box = layout.column().box()

        box.enabled = enable_this
        col = box.column()
        col.label(text="Distribute with gap")

        col.prop(context.window_manager.dmx, "dist_gap")
        col.prop(dmx, "fixtures_sorting_order")

        col = box.column_flow(columns=3, align=True)

        distributeGapX = col.operator("dmx.distribute_with_gap", text="X")
        distributeGapX.axis = "x"

        distributeGapY = col.operator("dmx.distribute_with_gap", text="Y")
        distributeGapY.axis = "y"

        distributeGapZ = col.operator("dmx.distribute_with_gap", text="Z")
        distributeGapZ.axis = "z"

        box = layout.column().box()
        box.enabled = enable_this
        col = box.column()
        col.label(text="Distribute in circle")

        col.prop(context.window_manager.dmx, "dist_diameter")
        col.prop(context.window_manager.dmx, "dist_rotate")
        col.prop(dmx, "fixtures_sorting_order")

        col = box.column_flow(columns=3, align=True)

        distributeGapX = col.operator("dmx.distribute_circle", text="X")
        distributeGapX.axis = "x"

        distributeGapY = col.operator("dmx.distribute_circle", text="Y")
        distributeGapY.axis = "y"

        distributeGapZ = col.operator("dmx.distribute_circle", text="Z")
        distributeGapZ.axis = "z"
