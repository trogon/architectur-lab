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
# Set shade smooth
# --------------------------------------------------------------------
def set_smooth(myobject):
    # deactivate others
    for o in bpy.data.objects:
        if o.select is True:
            o.select = False

    myobject.select = True
    bpy.context.scene.objects.active = myobject
    if bpy.context.scene.objects.active.name == myobject.name:
        bpy.ops.object.shade_smooth()

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
# Adds material, creates new if material not exists
# --------------------------------------------------------------------
def set_material(ob, matname, index = 0):
    # Get material
    mat = bpy.data.materials.get(matname)
    if mat is None:
        # create material
        mat = bpy.data.materials.new(name=matname)
    # Assign it to object
    if ob.data.materials:
        # assign to (index) material slot
        ob.data.materials[index] = mat
    else:
        # no slots
        ob.data.materials.append(mat)
    return mat

# --------------------------------------------------------------------
# Adds solidify modifier
# --------------------------------------------------------------------
def set_modifier_solidify(myobject, width, modname = "Solidify ArchLib"):
    modid = myobject.modifiers.find(modname)
    if (modid == -1):
        mod = myobject.modifiers.new(name=modname, type="SOLIDIFY")
    else:
        mod = myobject.modifiers[modname]
    mod.thickness = width
    mod.offset = 0
    mod.use_even_offset = True
    mod.use_quality_normals = True

# --------------------------------------------------------------------
# Adds subdivision modifier
# --------------------------------------------------------------------
def set_modifier_subsurf(myobject, modname = "Subsurf ArchLib"):
    modid = myobject.modifiers.find(modname)
    if (modid == -1):
        mod = myobject.modifiers.new(name=modname, type="SUBSURF")
    else:
        mod = myobject.modifiers[modname]
    mod.levels = 1
    mod.render_levels = 2

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
