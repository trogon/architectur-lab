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
from math import sin, cos, radians
from mathutils import Vector, Matrix

# --------------------------------------------------------------------
# Set normals
# True = faces to inside
# --------------------------------------------------------------------
def set_normals(myobject, direction=False):
    bpy.context.scene.objects.active = myobject
    # go edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    # select all faces
    bpy.ops.mesh.select_all(action='SELECT')
    # recalculate outside normals
    bpy.ops.mesh.normals_make_consistent(inside=direction)
    # go object mode again
    bpy.ops.object.editmode_toggle()

# --------------------------------------------------------------------
# Remove doubles
# --------------------------------------------------------------------
def remove_doubles(myobject):
    bpy.context.scene.objects.active = myobject
    # go edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    # select all faces
    bpy.ops.mesh.select_all(action='SELECT')
    # remove
    bpy.ops.mesh.remove_doubles()
    # go object mode again
    bpy.ops.object.editmode_toggle()

# --------------------------------------------------------------------
# Add modifier (solidify)
# --------------------------------------------------------------------
def set_modifier_solidify(myobject, width):
    bpy.context.scene.objects.active = myobject
    if bpy.context.scene.objects.active.name == myobject.name:
        bpy.ops.object.modifier_add(type='SOLIDIFY')
        for mod in myobject.modifiers:
            if mod.type == 'SOLIDIFY':
                mod.thickness = width
                mod.offset = 0
                mod.use_even_offset = True
                mod.use_quality_normals = True
                break

# --------------------------------------------------------------------
# Rotates a point in 2D space with specified angle
# --------------------------------------------------------------------
def rotate_point2d(posx, posy, angle):
    v1 = Vector([posx, posy])
    rada1 = radians(angle)
    cosa1 = cos(rada1)
    sina1 = sin(rada1)
    mat1 = Matrix([[cosa1, -sina1],
                    [sina1, cosa1]])
    v2 = mat1 * v1
    return v2

# --------------------------------------------------------------------
# Extracts vertices from selected object
# --------------------------------------------------------------------
def extract_vertices():
    print("".join(["[", ",".join(str(v.co).replace("<Vector ", "").replace(">", "") for v in bpy.context.object.data.vertices), "]"]))

# --------------------------------------------------------------------
# Extracts faces from selected object
# --------------------------------------------------------------------
def extract_faces():
    print("".join(["[(", "),(".join(",".join(str(v) for v in p.vertices) for p in bpy.context.object.data.polygons), ")]"]))
