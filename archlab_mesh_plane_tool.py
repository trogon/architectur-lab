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
from bpy.props import FloatProperty, CollectionProperty
from .archlab_utils import *

# ------------------------------------------------------------------------------
# Create main object for the plane.
# ------------------------------------------------------------------------------
def create_plane(self, context):
    # deselect all objects
    for o in bpy.data.objects:
        o.select = False

    # we create main object and mesh for walls
    planemesh = bpy.data.meshes.new("Plane")
    planeobject = bpy.data.objects.new("Plane", planemesh)
    planeobject.location = bpy.context.scene.cursor_location
    bpy.context.scene.objects.link(planeobject)
    planeobject.ArchLabPlaneGenerator.add()

    # we shape the walls and create other objects as children of 'PlaneObject'.
    shape_plane_mesh(planeobject, planemesh)

    # we select, and activate, main object for the plane.
    planeobject.select = True
    bpy.context.scene.objects.active = planeobject

# ------------------------------------------------------------------------------
# Shapes mesh and creates modifier solidify (the modifier, only the first time).
# ------------------------------------------------------------------------------
def shape_plane_mesh(myplane, tmp_mesh, update=False):
    pp = myplane.ArchLabPlaneGenerator[0]  # "pp" means "plane properties".
    mybase = None
    myfloor = None
    myceiling = None
    myshell = None
    # Create plane mesh data
    update_plane_mesh_data(tmp_mesh, get_blendunits(pp.plane_width), get_blendunits(pp.plane_height))
    myplane.data = tmp_mesh

    remove_doubles(myplane)
    set_normals(myplane)

    if pp.plane_depth > 0.0:
        if update is False or is_solidify(myplane) is False:
            set_modifier_solidify(myplane, get_blendunits(pp.plane_depth))
        else:
            for mod in myplane.modifiers:
                if mod.type == 'SOLIDIFY':
                    mod.thickness = pp.plane_depth
        # Move to Top SOLIDIFY
        movetotopsolidify(myplane)

    else:  # clear not used SOLIDIFY
        for mod in myplane.modifiers:
            if mod.type == 'SOLIDIFY':
                myplane.modifiers.remove(mod)

    # deactivate others
    for o in bpy.data.objects:
        if o.select is True and o.name != myplane.name:
            o.select = False

# ------------------------------------------------------------------------------
# Creates plane mesh data.
# ------------------------------------------------------------------------------
def update_plane_mesh_data(mymesh, width, height):
    lastx = -width /2
    lasty = -height /2
    sizex = width
    sizey = height

    myvertex = [(lastx, lasty, 0.0), (-lastx, lasty, 0.0)]
    myfaces = []
    lastface = 0

    myvertex.extend([(lastx, lasty + sizey, 0.0),
                    (lastx + sizex, lasty + sizey, 0.0)])

    myfaces.extend([(lastface, lastface + 1, lastface + 3, lastface + 2)])

    mymesh.from_pydata(myvertex, [], myfaces)
    mymesh.update(calc_edges=True)

# ------------------------------------------------------------------------------
# Update wall mesh and children objects (baseboard, floor and ceiling).
# ------------------------------------------------------------------------------
def update_plane(self, context):
    # When we update, the active object is the main object of the plane.
    o = bpy.context.active_object
    oldmesh = o.data
    oldname = o.data.name
    # Now we deselect that plane object to not delete it.
    o.select = False
    # and we create a new mesh for the plane:
    tmp_mesh = bpy.data.meshes.new("temp")
    # deselect all objects
    for obj in bpy.data.objects:
        obj.select = False
    # Finally we shape the main mesh again\,
    shape_plane_mesh(o, tmp_mesh, True)
    o.data = tmp_mesh
    # Remove data (mesh of active object),
    bpy.data.meshes.remove(oldmesh)
    tmp_mesh.name = oldname
    # and select, and activate, the main object of the plane.
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


# ------------------------------------------------------------------
# Define property group class to create or modify a planes.
# ------------------------------------------------------------------
class ArchLabPlaneProperties(PropertyGroup):
    plane_height = FloatProperty(
            name='Height',
            default=1.0, precision=3,
            description='Plane height', update=update_plane,
            )
    plane_width = FloatProperty(
            name='Width',
            default=1.0, precision=3,
            description='Plane width', update=update_plane,
            )
    plane_depth = FloatProperty(
            name='Thickness',
            default=0.0, precision=4,
            description='Thickness of the plane', update=update_plane,
            )

bpy.utils.register_class(ArchLabPlaneProperties)
Object.ArchLabPlaneGenerator = CollectionProperty(type=ArchLabPlaneProperties)

# ------------------------------------------------------------------
# Define panel class to modify planes.
# ------------------------------------------------------------------
class ArchLabPlaneGeneratorPanel(Panel):
    bl_idname = "OBJECT_PT_plane_generator"
    bl_label = "Plane"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'ArchLab'

    # -----------------------------------------------------
    # Verify if visible
    # -----------------------------------------------------
    @classmethod
    def poll(cls, context):
        o = context.object
        if o is None:
            return False
        if 'ArchLabPlaneGenerator' not in o:
            return False
        else:
            return True

    # -----------------------------------------------------
    # Draw (create UI interface)
    # -----------------------------------------------------
    def draw(self, context):
        o = context.object
        # If the selected object didn't be created with the group 'ArchLabPlaneGenerator', this panel is not created.
        try:
            if 'ArchLabPlaneGenerator' not in o:
                return
        except:
            return

        layout = self.layout
        if bpy.context.mode == 'EDIT_MESH':
            layout.label('Warning: Operator does not work in edit mode.', icon='ERROR')
        else:
            plane = o.ArchLabPlaneGenerator[0]
            row = layout.row()
            row.prop(plane, 'plane_width')
            row = layout.row()
            row.prop(plane, 'plane_height')
            row = layout.row()
            row.prop(plane, 'plane_depth')

# ------------------------------------------------------------------
# Define operator class to create planes
# ------------------------------------------------------------------
class ArchLabPlane(Operator):
    bl_idname = "mesh.archlab_plane"
    bl_label = "Plane"
    bl_description = "Generate plane with walls, baseboard, floor and ceiling"
    bl_category = 'ArchLab'
    bl_options = {'REGISTER', 'UNDO'}

    # -----------------------------------------------------
    # Draw (create UI interface)
    # -----------------------------------------------------
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label("Use Properties panel (N) to define parms", icon='INFO')

    # -----------------------------------------------------
    # Execute
    # -----------------------------------------------------
    def execute(self, context):
        if bpy.context.mode == "OBJECT":
            create_plane(self, context)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "ArchLab: Option only valid in Object mode")
            return {'CANCELLED'}
