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
from .archlab_utils import *

# ------------------------------------------------------------------------------
# Create main object for the uvsphere.
# ------------------------------------------------------------------------------
def create_uvsphere(self, context):
    # deselect all objects
    for o in bpy.data.objects:
        o.select = False

    # we create main object and mesh for uvsphere
    uvspheremesh = bpy.data.meshes.new("UvSphere")
    uvsphereobject = bpy.data.objects.new("UvSphere", uvspheremesh)
    uvsphereobject.location = bpy.context.scene.cursor_location
    bpy.context.scene.objects.link(uvsphereobject)
    uvsphereobject.ArchLabUvSphereGenerator.add()

    uvsphereobject.ArchLabUvSphereGenerator[0].uvsphere_radius = self.uvsphere_radius
    uvsphereobject.ArchLabUvSphereGenerator[0].uvsphere_segments = self.uvsphere_segments
    uvsphereobject.ArchLabUvSphereGenerator[0].uvsphere_rings = self.uvsphere_rings

    # we shape the mesh.
    shape_uvsphere_mesh(uvsphereobject, uvspheremesh)

    # we select, and activate, main object for the uvsphere.
    uvsphereobject.select = True
    bpy.context.scene.objects.active = uvsphereobject

# ------------------------------------------------------------------------------
# Shapes mesh the uvsphere mesh
# ------------------------------------------------------------------------------
def shape_uvsphere_mesh(myuvsphere, tmp_mesh, update=False):
    usp = myuvsphere.ArchLabUvSphereGenerator[0]  # "usp" means "uvsphere properties".
    # Create uvsphere mesh data
    update_uvsphere_mesh_data(tmp_mesh, usp.uvsphere_radius, usp.uvsphere_segments, usp.uvsphere_rings)
    myuvsphere.data = tmp_mesh

    remove_doubles(myuvsphere)
    set_normals(myuvsphere)

    # deactivate others
    for o in bpy.data.objects:
        if o.select is True and o.name != myuvsphere.name:
            o.select = False

# ------------------------------------------------------------------------------
# Creates uvsphere mesh data.
# ------------------------------------------------------------------------------
def update_uvsphere_mesh_data(mymesh, radius, segments, rings):
    sDeltaAngle = 360 /segments
    rDeltaAngle = 180 /rings

    myvertex = []
    myfaces = []
    
    for tr in range(rings +1):
        v1 = rotate_point2d(0.0, radius, tr * rDeltaAngle)
        for ts in range(segments):
            v2 = rotate_point2d(v1[0], 0.0, ts * sDeltaAngle)
            p = (v2[0], v2[1], v1[1])
            myvertex.append(p)
            if tr > 0:
                myfaces.append([(tr -1) * segments + ts,
                                (tr -1) * segments + ((ts +1) % segments),
                                tr * segments + ((ts +1) % segments),
                                tr * segments + ts])

    mymesh.from_pydata(myvertex, [], myfaces)
    mymesh.update(calc_edges=True)

# ------------------------------------------------------------------------------
# Update uvsphere mesh.
# ------------------------------------------------------------------------------
def update_uvsphere(self, context):
    # When we update, the active object is the main object of the uvsphere.
    o = bpy.context.active_object
    oldmesh = o.data
    oldname = o.data.name
    # Now we deselect that uvsphere object to not delete it.
    o.select = False
    # and we create a new mesh for the uvsphere:
    tmp_mesh = bpy.data.meshes.new("temp")
    # deselect all objects
    for obj in bpy.data.objects:
        obj.select = False
    # Finally we shape the main mesh again,
    shape_uvsphere_mesh(o, tmp_mesh, True)
    o.data = tmp_mesh
    # Remove data (mesh of active object),
    bpy.data.meshes.remove(oldmesh)
    tmp_mesh.name = oldname
    # and select, and activate, the main object of the uvsphere.
    o.select = True
    bpy.context.scene.objects.active = o

# -----------------------------------------------------
# Property definition creator
# -----------------------------------------------------
def uvsphere_radius_property():
    return FloatProperty(
            name='Radius',
            default=1.0, precision=3, unit = 'LENGTH',
            description='UV Sphere radius', update=update_uvsphere,
            )

def uvsphere_segments_property():
    return IntProperty(
            name='Segments',
            min=3, max=1000,
            default=32,
            description='UV Sphere segments amount', update=update_uvsphere,
            )

def uvsphere_rings_property():
    return IntProperty(
            name='Rings',
            min=2, max=1000,
            default=16,
            description='UV Sphere rings amount', update=update_uvsphere,
            )

# ------------------------------------------------------------------
# Define property group class to create or modify a uvspheres.
# ------------------------------------------------------------------
class ArchLabUvSphereProperties(PropertyGroup):
    uvsphere_radius = uvsphere_radius_property()
    uvsphere_segments = uvsphere_segments_property()
    uvsphere_rings = uvsphere_rings_property()

bpy.utils.register_class(ArchLabUvSphereProperties)
Object.ArchLabUvSphereGenerator = CollectionProperty(type=ArchLabUvSphereProperties)

# ------------------------------------------------------------------
# Define panel class to modify uvspheres.
# ------------------------------------------------------------------
class ArchLabUvSphereGeneratorPanel(Panel):
    bl_idname = "OBJECT_PT_uvsphere_generator"
    bl_label = "UvSphere"
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
        if 'ArchLabUvSphereGenerator' not in o:
            return False
        if act_op is not None and act_op.bl_idname.endswith('archlab_uv_sphere'):
            return False
        else:
            return True

    # -----------------------------------------------------
    # Draw (create UI interface)
    # -----------------------------------------------------
    def draw(self, context):
        o = context.object
        # If the selected object didn't be created with the group 'ArchLabUvSphereGenerator', this panel is not created.
        try:
            if 'ArchLabUvSphereGenerator' not in o:
                return
        except:
            return

        layout = self.layout
        if bpy.context.mode == 'EDIT_MESH':
            layout.label('Warning: Operator does not work in edit mode.', icon='ERROR')
        else:
            uvsphere = o.ArchLabUvSphereGenerator[0]
            row = layout.row()
            row.prop(uvsphere, 'uvsphere_radius')
            row = layout.row()
            row.prop(uvsphere, 'uvsphere_segments')
            row = layout.row()
            row.prop(uvsphere, 'uvsphere_rings')

# ------------------------------------------------------------------
# Define operator class to create uvspheres
# ------------------------------------------------------------------
class ArchLabUvSphere(Operator):
    bl_idname = "mesh.archlab_uv_sphere"
    bl_label = "UvSphere"
    bl_description = "Generate uvsphere primitive mesh"
    bl_category = 'ArchLab'
    bl_options = {'REGISTER', 'UNDO'}

    # preset
    uvsphere_radius = uvsphere_radius_property()
    uvsphere_segments = uvsphere_segments_property()
    uvsphere_rings = uvsphere_rings_property()

    # -----------------------------------------------------
    # Draw (create UI interface)
    # -----------------------------------------------------
    def draw(self, context):
        layout = self.layout
        space = bpy.context.space_data
        if not space.local_view:
            row = layout.row()
            row.prop(self, 'uvsphere_radius')
            row = layout.row()
            row.prop(self, 'uvsphere_segments')
            row = layout.row()
            row.prop(self, 'uvsphere_rings')
        else:
            row = layout.row()
            row.label("Warning: Operator does not work in local view mode", icon='ERROR')

    # -----------------------------------------------------
    # Execute
    # -----------------------------------------------------
    def execute(self, context):
        if bpy.context.mode == "OBJECT":
            space = bpy.context.space_data
            if not space.local_view:
                create_uvsphere(self, context)
                return {'FINISHED'}
            else:
                self.report({'WARNING'}, "ArchLab: Option only valid in global view mode")
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, "ArchLab: Option only valid in Object mode")
            return {'CANCELLED'}
