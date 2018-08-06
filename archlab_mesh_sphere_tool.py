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
from bpy.props import EnumProperty, IntProperty, FloatProperty, CollectionProperty
from math import sqrt
from .archlab_utils import *

# ------------------------------------------------------------------------------
# Create main object for the sphere.
# ------------------------------------------------------------------------------
def create_sphere(self, context):
    # deselect all objects
    for o in bpy.data.objects:
        o.select = False

    # we create main object and mesh for sphere
    spheremesh = bpy.data.meshes.new("Sphere")
    sphereobject = bpy.data.objects.new("Sphere", spheremesh)
    sphereobject.location = bpy.context.scene.cursor_location
    bpy.context.scene.objects.link(sphereobject)
    sphereobject.ArchLabSphereGenerator.add()

    sphereobject.ArchLabSphereGenerator[0].sphere_radius = self.sphere_radius
    sphereobject.ArchLabSphereGenerator[0].sphere_type = self.sphere_type
    sphereobject.ArchLabSphereGenerator[0].sphere_segments = self.sphere_segments
    sphereobject.ArchLabSphereGenerator[0].sphere_rings = self.sphere_rings
    sphereobject.ArchLabSphereGenerator[0].sphere_subdivisions = self.sphere_subdivisions

    # we shape the mesh.
    shape_sphere_mesh(sphereobject, spheremesh)

    # we select, and activate, main object for the sphere.
    sphereobject.select = True
    bpy.context.scene.objects.active = sphereobject

# ------------------------------------------------------------------------------
# Shapes mesh the sphere mesh
# ------------------------------------------------------------------------------
def shape_sphere_mesh(mysphere, tmp_mesh, update=False):
    sp = mysphere.ArchLabSphereGenerator[0]  # "sp" means "sphere properties".
    # Create sphere mesh data
    update_sphere_mesh_data(tmp_mesh, sp.sphere_radius, sp.sphere_type, sp.sphere_segments, sp.sphere_rings, sp.sphere_subdivisions)
    mysphere.data = tmp_mesh

    remove_doubles(mysphere)
    set_normals(mysphere)

    # deactivate others
    for o in bpy.data.objects:
        if o.select is True and o.name != mysphere.name:
            o.select = False

# ------------------------------------------------------------------------------
# Creates sphere mesh data.
# ------------------------------------------------------------------------------
def update_sphere_mesh_data(mymesh, radius, type, segments, rings, subdivisions):
    myvertex = []
    myfaces = []
    
    if type == 'UV':
        segv = range(segments)
        sDeltaAngle = 360 /segments
        rDeltaAngle = 180 /rings
        p = (0.0, 0.0, radius)
        lastr = 0
        for tr in range(rings +1):
            lastv = segv[-1]
            for ts in segv:
                p1 = rotate_point3d(p, anglex=(tr * rDeltaAngle), anglez=(ts * sDeltaAngle))
                myvertex.append(p1)
                if tr > 0:
                    myfaces.append((
                        lastr * segments + lastv,
                        lastr * segments + ts,
                        tr * segments + ts,
                        tr * segments + lastv
                    ))
                    lastv = ts
            lastr = tr

    if type == 'ICO':
        segments = 5
        topv = range(1, segments + 1)
        botv = range(segments + 1, segments * 2 + 1)
        sDeltaAngle = 360 /segments
        p1 = (0.2764 * radius, 0.8506 * radius, 0.4472 * radius)
        p2 = (0.7236 * radius, 0.5257 * radius, -0.4472 * radius)

        myvertex.append((0.0000, 0.0000, radius))
        lastv = topv[-1]
        for ts in topv:
            v1 = rotate_point3d(p1, anglez=(ts * sDeltaAngle))
            myvertex.append(v1)
            myfaces.append((0, lastv, ts))
            myfaces.append((lastv, ts, ts + segments))
            lastv = ts
        lastv = botv[-1]
        for ts in botv:
            v1 = rotate_point3d(p2, anglez=(ts * sDeltaAngle))
            myvertex.append(v1)
            myfaces.append((lastv, ts, lastv - segments))
            myfaces.append((11, lastv, ts))
            lastv = ts
        myvertex.append((0.0000, 0.0000, -radius))
        for ts in range(1, subdivisions):
            (myvertex, myfaces) = subdivide_mesh(myvertex, myfaces)


    mymesh.from_pydata(myvertex, [], myfaces)
    mymesh.update(calc_edges=True)

# ------------------------------------------------------------------------------
# Update sphere mesh.
# ------------------------------------------------------------------------------
def update_sphere(self, context):
    # When we update, the active object is the main object of the sphere.
    o = bpy.context.active_object
    oldmesh = o.data
    oldname = o.data.name
    # Now we deselect that sphere object to not delete it.
    o.select = False
    # and we create a new mesh for the sphere:
    tmp_mesh = bpy.data.meshes.new("temp")
    # deselect all objects
    for obj in bpy.data.objects:
        obj.select = False
    # Finally we shape the main mesh again,
    shape_sphere_mesh(o, tmp_mesh, True)
    o.data = tmp_mesh
    # Remove data (mesh of active object),
    bpy.data.meshes.remove(oldmesh)
    tmp_mesh.name = oldname
    # and select, and activate, the main object of the sphere.
    o.select = True
    bpy.context.scene.objects.active = o

# -----------------------------------------------------
# Subdivide circle mesh
# -----------------------------------------------------
def subdivide_mesh(verts, faces):
    myverts = verts
    myfaces = []
    vertnum = len(faces)
    for f in faces:
        laste = f[-1]
        newface = []
        for ts in range(len(f)):
            v1 = slide_point3d(verts[laste], verts[f[ts]], 0.5)
            v1.normalize()
            newface.append(len(myverts))
            myverts.append(v1)
            laste = f[ts]
        myfaces.append((newface[0], newface[1], newface[2]))
        myfaces.append((newface[0], newface[1], f[0]))
        myfaces.append((newface[1], newface[2], f[1]))
        myfaces.append((newface[2], newface[0], f[2]))
    #myfaces.extend(faces)
    return myverts, myfaces

# -----------------------------------------------------
# Property definition creator
# -----------------------------------------------------
def sphere_radius_property():
    return FloatProperty(
            name='Radius',
            default=1.0, precision=3, unit = 'LENGTH',
            description='Sphere radius', update=update_sphere,
            )

def sphere_type_property(defaultitem = 'UV'):
    return EnumProperty(
            items=(
                ('UV', 'UV Sphere', ''),
                ('ICO', 'Ico Sphere', ''),
                ),
            name='Topology type',
            default=defaultitem,
            description='Topology of sphere mesh', update=update_sphere,
            )

def sphere_segments_property():
    return IntProperty(
            name='Segments',
            min=3, max=1000, soft_max=200,
            default=32,
            description='UV Sphere segments amount', update=update_sphere,
            )

def sphere_rings_property():
    return IntProperty(
            name='Rings',
            min=2, max=1000, soft_max=100,
            default=16,
            description='UV Sphere rings amount', update=update_sphere,
            )

def sphere_subdivisions_property():
    return IntProperty(
            name='Subdivisions',
            min=1, max=10, soft_max=8,
            default=2,
            description='Ico Sphere subdivisions amount', update=update_sphere,
            )

# ------------------------------------------------------------------
# Define property group class to create or modify a spheres.
# ------------------------------------------------------------------
class ArchLabSphereProperties(PropertyGroup):
    sphere_radius = sphere_radius_property()
    sphere_type = sphere_type_property()
    sphere_segments = sphere_segments_property()
    sphere_rings = sphere_rings_property()
    sphere_subdivisions = sphere_subdivisions_property()

bpy.utils.register_class(ArchLabSphereProperties)
Object.ArchLabSphereGenerator = CollectionProperty(type=ArchLabSphereProperties)

# ------------------------------------------------------------------
# Define panel class to modify spheres.
# ------------------------------------------------------------------
class ArchLabSphereGeneratorPanel(Panel):
    bl_idname = "OBJECT_PT_sphere_generator"
    bl_label = "Sphere"
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
        if 'ArchLabSphereGenerator' not in o:
            return False
        if act_op is not None and act_op.bl_idname.endswith('archlab_sphere'):
            return False
        else:
            return True

    # -----------------------------------------------------
    # Draw (create UI interface)
    # -----------------------------------------------------
    def draw(self, context):
        o = context.object
        # If the selected object didn't be created with the group 'ArchLabSphereGenerator', this panel is not created.
        try:
            if 'ArchLabSphereGenerator' not in o:
                return
        except:
            return

        layout = self.layout
        if bpy.context.mode == 'EDIT_MESH':
            layout.label('Warning: Operator does not work in edit mode.', icon='ERROR')
        else:
            sphere = o.ArchLabSphereGenerator[0]
            row = layout.row()
            row.prop(sphere, 'sphere_radius')
            row = layout.row()
            row.prop(sphere, 'sphere_type')
            if sphere.sphere_type == 'UV':
                row = layout.row()
                row.prop(sphere, 'sphere_segments')
                row = layout.row()
                row.prop(sphere, 'sphere_rings')
            if sphere.sphere_type == 'ICO':
                row = layout.row()
                row.prop(sphere, 'sphere_subdivisions')

# ------------------------------------------------------------------
# Define operator class to create spheres
# ------------------------------------------------------------------
class ArchLabSphere(Operator):
    bl_description = "Generate sphere primitive mesh"
    bl_category = 'ArchLab'
    bl_options = {'REGISTER', 'UNDO'}

    # -----------------------------------------------------
    # Draw (create UI interface)
    # -----------------------------------------------------
    def draw(self, context):
        layout = self.layout
        space = bpy.context.space_data
        if not space.local_view:
            row = layout.row()
            row.prop(self, 'sphere_radius')
            row = layout.row()
            row.prop(self, 'sphere_type')
            if self.sphere_type == 'UV':
                row = layout.row()
                row.prop(self, 'sphere_segments')
                row = layout.row()
                row.prop(self, 'sphere_rings')
            if self.sphere_type == 'ICO':
                row = layout.row()
                row.prop(self, 'sphere_subdivisions')
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
                create_sphere(self, context)
                return {'FINISHED'}
            else:
                self.report({'WARNING'}, "ArchLab: Option only valid in global view mode")
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, "ArchLab: Option only valid in Object mode")
            return {'CANCELLED'}


# ------------------------------------------------------------------
# Define operator class to create spheres
# ------------------------------------------------------------------
class ArchLabUvSphere(ArchLabSphere):
    bl_idname = "mesh.archlab_uvsphere"
    bl_label = "Add UV Sphere"

    # preset
    sphere_radius = sphere_radius_property()
    sphere_type = sphere_type_property('UV')
    sphere_segments = sphere_segments_property()
    sphere_rings = sphere_rings_property()
    sphere_subdivisions = sphere_subdivisions_property()


# ------------------------------------------------------------------
# Define operator class to create spheres
# ------------------------------------------------------------------
class ArchLabIcoSphere(ArchLabSphere):
    bl_idname = "mesh.archlab_icosphere"
    bl_label = "Add Ico Sphere"

    # preset
    sphere_radius = sphere_radius_property()
    sphere_type = sphere_type_property('ICO')
    sphere_segments = sphere_segments_property()
    sphere_rings = sphere_rings_property()
    sphere_subdivisions = sphere_subdivisions_property()
