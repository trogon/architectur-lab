# ##### BEGIN MIT LICENSE BLOCK #####
# MIT License
# 
# Copyright (c) 2018 Insma Software
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ##### END MIT LICENSE BLOCK #####

# ----------------------------------------------------------
# Author: Maciej Klemarczyk (mklemarczyk)
# ----------------------------------------------------------
import bpy
from bpy.types import Operator, PropertyGroup, Object, Panel
from bpy.props import IntProperty, FloatProperty, CollectionProperty
from .archlab_bldn_wall_tool import ArchLabWallProperties
from .archlab_utils import *

# ------------------------------------------------------------------------------
# Create main object for the room.
# ------------------------------------------------------------------------------
def create_room(self, context):
    # deselect all objects
    for o in bpy.data.objects:
        o.select = False

    # we create main object and mesh for room
    roommesh = bpy.data.meshes.new("Room")
    roomobject = bpy.data.objects.new("Room", roommesh)
    roomobject.location = bpy.context.scene.cursor_location
    bpy.context.scene.objects.link(roomobject)
    roomobject.ArchLabRoomGenerator.add()

    roomobject.ArchLabRoomGenerator[0].room_height = self.room_height
    roomobject.ArchLabRoomGenerator[0].room_wall_count = self.room_wall_count
    for wall in self.room_walls:
        wallprop = roomobject.ArchLabRoomGenerator[0].room_walls.add()
        wallprop.wall_width = wall.wall_width
        wallprop.wall_depth = wall.wall_depth
        wallprop.wall_angle = wall.wall_angle

    # we shape the mesh.
    shape_room_mesh(roomobject, roommesh)

    # we select, and activate, main object for the room.
    roomobject.select = True
    bpy.context.scene.objects.active = roomobject

# ------------------------------------------------------------------------------
# Shapes mesh and creates modifier solidify (the modifier, only the first time).
# ------------------------------------------------------------------------------
def shape_room_mesh(myroom, tmp_mesh, update=False):
    rp = myroom.ArchLabRoomGenerator[0]  # "rp" means "room properties".

    drwc = len(rp.room_walls)
    prwc = rp.room_wall_count
    if not drwc == prwc:
        wdif = prwc - drwc
        if wdif > 0:
            for t in range(wdif):
                rp.room_walls.add()
        if wdif < 0:
            for t in range(-wdif):
                rp.room_walls.remove(prwc)

    # Create room mesh data
    update_room_mesh_data(tmp_mesh, rp.room_height, rp.room_walls)
    myroom.data = tmp_mesh

    remove_doubles(myroom)
    set_normals(myroom)

    if rp.room_wall_depth > 0.0:
        if update is False or is_solidify(myroom) is False:
            set_modifier_solidify(myroom, rp.room_wall_depth)
        else:
            for mod in myroom.modifiers:
                if mod.type == 'SOLIDIFY':
                    mod.thickness = rp.room_wall_depth
                    mod.use_even_offset = False # The solidify have a problem with some wall angles
        # Move to Top SOLIDIFY
        movetotopsolidify(myroom)

    else:  # clear not used SOLIDIFY
        for mod in myroom.modifiers:
            if mod.type == 'SOLIDIFY':
                myroom.modifiers.remove(mod)

    # deactivate others
    for o in bpy.data.objects:
        if o.select is True and o.name != myroom.name:
            o.select = False

# ------------------------------------------------------------------------------
# Creates room mesh data.
# ------------------------------------------------------------------------------
def update_room_mesh_data(mymesh, height, walls):
    myvertices = []
    myfaces = []

    if len(walls) > 0:
        myvertices = [(0.0, 0.0, 0.0), (0.0, 0.0, height)]
    lastwi = 0
    lastp = [0.0, 0.0, 0.0]
    lastpnorm = [1.0, 0.0, 0.0]
    for wall in walls:
        pnorm = rotate_point3d_rad(lastpnorm, anglez=wall.wall_angle)
        p1 = [
            lastp[0] + pnorm[0] * wall.wall_width,
            lastp[1] + pnorm[1] * wall.wall_width,
            lastp[2] + pnorm[2] * wall.wall_width
        ]
        myvertices.extend([(p1[0], p1[1], 0.0), (p1[0], p1[1], height)])
        myfaces.append((lastwi * 2 + 0, lastwi * 2 + 1, lastwi * 2 + 3, lastwi * 2 + 2))
        lastwi = lastwi + 1
        lastp = p1
        lastpnorm = pnorm

    mymesh.from_pydata(myvertices, [], myfaces)
    mymesh.update(calc_edges=True)

# ------------------------------------------------------------------------------
# Update room mesh.
# ------------------------------------------------------------------------------
def update_room(self, context):
    # When we update, the active object is the main object of the room.
    o = bpy.context.active_object
    oldmesh = o.data
    oldname = o.data.name
    # Now we deselect that room object to not delete it.
    o.select = False
    # and we create a new mesh for the room:
    tmp_mesh = bpy.data.meshes.new("temp")
    # deselect all objects
    for obj in bpy.data.objects:
        obj.select = False
    # Finally we shape the main mesh again,
    shape_room_mesh(o, tmp_mesh, True)
    o.data = tmp_mesh
    # Remove data (mesh of active object),
    bpy.data.meshes.remove(oldmesh)
    tmp_mesh.name = oldname
    # and select, and activate, the main object of the room.
    o.select = True
    bpy.context.scene.objects.active = o

# -----------------------------------------------------
# Verify if solidify exist
# -----------------------------------------------------
def is_solidify(myobject):
    flag = False
    try:
        if myobject.modifiers is None:
            return False

        for mod in myobject.modifiers:
            if mod.type == 'SOLIDIFY':
                flag = True
                break
        return flag
    except AttributeError:
        return False

# -----------------------------------------------------
# Move Solidify to Top
# -----------------------------------------------------
def movetotopsolidify(myobject):
    mymod = None
    try:
        if myobject.modifiers is not None:
            for mod in myobject.modifiers:
                if mod.type == 'SOLIDIFY':
                    mymod = mod

            if mymod is not None:
                while myobject.modifiers[0] != mymod:
                    bpy.ops.object.modifier_move_up(modifier=mymod.name)
    except AttributeError:
        return

# -----------------------------------------------------
# Property definition creator
# -----------------------------------------------------
def room_height_property(callback=None):
    return FloatProperty(
            name='Height',
            soft_min=0.001,
            default=2.5, precision=3, unit = 'LENGTH',
            description='Room height', update=callback,
            )

def room_wall_count_property(callback=None):
    return IntProperty(
            name='Wall count',
            min=1, soft_max=1000,
            default=1,
            description='Number of walls in the room', update=callback,
            )

def room_wall_depth_property(callback=None):
    return FloatProperty(
            name='Thickness',
            soft_min=0.001,
            default=0.025, precision=4, unit = 'LENGTH',
            description='Thickness of the walls', update=callback,
            )

def room_walls_property(callback=None):
    return CollectionProperty(type=ArchLabWallProperties)

# ------------------------------------------------------------------
# Define property group class to create or modify a rooms.
# ------------------------------------------------------------------
class ArchLabRoomProperties(PropertyGroup):
    room_height = room_height_property(callback=update_room)
    room_wall_count = room_wall_count_property(callback=update_room)
    room_wall_depth = room_wall_depth_property(callback=update_room)
    room_walls = room_walls_property(callback=update_room)

bpy.utils.register_class(ArchLabRoomProperties)
Object.ArchLabRoomGenerator = CollectionProperty(type=ArchLabRoomProperties)

# ------------------------------------------------------------------
# Define panel class to modify rooms.
# ------------------------------------------------------------------
class ArchLabRoomGeneratorPanel(Panel):
    bl_idname = "OBJECT_PT_room_generator"
    bl_label = "Room"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'ArchLab'

    # -----------------------------------------------------
    # Verify if visible
    # -----------------------------------------------------
    @classmethod
    def poll(cls, context):
        o = context.object
        act_op = context.active_operator
        if o is None:
            return False
        if 'ArchLabRoomGenerator' not in o:
            return False
        if act_op is not None and act_op.bl_idname.endswith('archlab_room'):
            return False
        else:
            return True

    # -----------------------------------------------------
    # Draw (create UI interface)
    # -----------------------------------------------------
    def draw(self, context):
        o = context.object
        # If the selected object didn't be created with the group 'ArchLabRoomGenerator', this panel is not created.
        try:
            if 'ArchLabRoomGenerator' not in o:
                return
        except:
            return

        layout = self.layout
        if bpy.context.mode == 'EDIT_MESH':
            layout.label('Warning: Operator does not work in edit mode.', icon='ERROR')
        else:
            room = o.ArchLabRoomGenerator[0]
            row = layout.row()
            row.prop(room, 'room_height')
            row = layout.row()
            row.prop(room, 'room_wall_count')
            for wt in range(len(room.room_walls)):
                box = layout.box()
                label = box.label('Wall %i' % (wt+1))
                row = box.row()
                row.prop(room.room_walls[wt], 'wall_width')
                row = box.row()
                row.prop(room.room_walls[wt], 'wall_angle')

# ------------------------------------------------------------------
# Define operator class to create rooms
# ------------------------------------------------------------------
class ArchLabRoom(Operator):
    bl_idname = "mesh.archlab_room"
    bl_label = "Add Room"
    bl_description = "Generate room mesh"
    bl_category = 'ArchLab'
    bl_options = {'REGISTER', 'UNDO'}

    # preset
    room_height = room_height_property()
    room_wall_count = room_wall_count_property()
    room_wall_depth = room_wall_depth_property()
    room_walls = CollectionProperty(type=ArchLabWallProperties)

    # -----------------------------------------------------
    # Draw (create UI interface)
    # -----------------------------------------------------
    def draw(self, context):
        layout = self.layout
        space = bpy.context.space_data
        if not space.local_view:
            row = layout.row()
            row.prop(self, 'room_height')
            row = layout.row()
            row.prop(self, 'room_wall_count')
            for wt in range(len(self.room_walls)):
                box = layout.box()
                label = box.label('Wall %i' % (wt+1))
                row = box.row()
                row.prop(self.room_walls[wt], 'wall_width')
                row = box.row()
                row.prop(self.room_walls[wt], 'wall_angle')
        else:
            row = layout.row()
            row.label("Warning: Operator does not work in local view mode", icon='ERROR')

    # -----------------------------------------------------
    # Execute
    # -----------------------------------------------------
    def execute(self, context):
        drwc = len(self.room_walls)
        prwc = self.room_wall_count
        if not drwc == prwc:
            wdif = prwc - drwc
            if wdif > 0:
                for t in range(wdif):
                    self.room_walls.add()
            if wdif < 0:
                for t in range(-wdif):
                    self.room_walls.remove(prwc)

        if bpy.context.mode == "OBJECT":
            space = bpy.context.space_data
            if not space.local_view:
                create_room(self, context)
                return {'FINISHED'}
            else:
                self.report({'WARNING'}, "ArchLab: Option only valid in global view mode")
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, "ArchLab: Option only valid in Object mode")
            return {'CANCELLED'}
