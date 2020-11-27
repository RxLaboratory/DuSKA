#====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#======================= END GPL LICENSE BLOCK ========================

# <pep8 compliant>

bl_info = {
    "name": "DuSKA - Shape Key Animator",
    "category": "Animation",
    "blender": (2, 80, 0),
    "author": "Nicolas 'Duduf' Dufresne",
    "location": "3D View > Sidebar > Item",
    "version": (1,0,0),
    "description": "Eases animation using shape keys (clay animation) and corrective shape keys.",
    "wiki_url": "https://duska-docs.rainboxlab.org/",
}

import bpy # pylint: disable=import-error
import importlib
from bpy.app.handlers import persistent # pylint: disable=import-error

from . import (
    dublf,
)

def is_shape_keyable(obj):
    if obj is None: return False
    return obj.type == 'CURVE' or obj.type == 'MESH'

def set_ska(shape_keys, index):
    for i, sk in enumerate(shape_keys):
        if not is_ska_key(sk): continue
        if i == index:
            sk.value = 1
            return
        else: sk.value = 0

def set_ska_values(shape_keys, indices, values):
    for i, index in enumerate(indices):
        sk = shape_keys[index]
        if not is_ska_key(sk): continue
        sk.value = values[i]

    for i, sk in enumerate(shape_keys):
        if not is_ska_key(sk): continue
        if i in indices: continue
        sk.value = 0

def update_ska_index(obj, context=bpy.context):
    """Updates the index of the Shape Key Animator"""
    if not is_shape_keyable(obj): return

    current_key = obj.ska_active_index

    shape_keys = obj.data.shape_keys.key_blocks
    
    # check if the index is animated, if so interpolate
    if dublf.animation.is_animated(obj):
        for fcurve in obj.animation_data.action.fcurves:
            if fcurve.data_path == 'ska_active_index':
                frame = context.scene.frame_current
                # find keyframes
                keyframes = fcurve.keyframe_points
                # Juste one keyframe
                if len(keyframes) < 2:
                    set_ska(shape_keys, current_key)
                    return
                # Get the previous key
                prev_key = dublf.animation.get_previous_keyframe(fcurve, frame)
                if prev_key is None:
                    set_ska(shape_keys, current_key)
                    return
                prev_key_time = prev_key.co[0]
                prev_key_value = prev_key.co[1]
                if prev_key.interpolation == 'CONSTANT':
                    set_ska(shape_keys, prev_key.co[1])
                    return
                # Interpolate
                next_key = dublf.animation.get_next_keyframe(fcurve, frame)
                if next_key is None:
                    set_ska(shape_keys, prev_key.co[1])
                    return
                next_key_time = next_key.co[0]
                next_key_value = next_key.co[1]
                t = frame - prev_key_time
                d = next_key_time - prev_key_time
                if d == 0:
                    ratio = 1
                else:
                    ratio = t / d
                set_ska_values(shape_keys, [ int(prev_key_value), int(next_key_value) ], [ 1-ratio, ratio ])
    else:
        set_ska(shape_keys, current_key)
        
def view_ska_index(obj, context):
    if not is_shape_keyable(obj): return
    current_key = obj.ska_active_index
    set_ska(obj.data.shape_keys.key_blocks, current_key)

def is_ska_key( shapeKey ):
    return 'SKA.'in shapeKey.name

@persistent
def update_keys_handler( scene ):
    """Updates all keys"""
    for obj in bpy.data.objects:
        update_ska_index(obj, bpy.context)

class DUSKA_OT_add_key( bpy.types.Operator ):
    bl_idname = "object.ska_add_key"
    bl_label = "Add Key"
    bl_description = "Adds a new Shape Key to be used in the animation"
    bl_options = {'REGISTER','UNDO'}

    from_mix: bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        obj = context.object
        return is_shape_keyable(obj)

    def execute(self, context):
        obj = context.object
        # Add a new key
        sk = obj.shape_key_add(name='SKA.Key', from_mix=self.from_mix)
        num_keys = len(obj.data.shape_keys.key_blocks)
        if num_keys == 1:
            sk.name = 'Basis'
            obj.shape_key_add(name='SKA.Key', from_mix=False)
        i = len(obj.data.shape_keys.key_blocks)-1
        obj.active_shape_key_index = i
        obj.ska_active_index = i
        
        return {'FINISHED'}

class DUSKA_OT_remove_key(bpy.types.Operator ):
    bl_idname = "object.ska_remove_key"
    bl_label = "Remove Key"
    bl_description = "Removes a new Shape Key to be used in the animation"
    bl_options = {'REGISTER','UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        if not is_shape_keyable(obj): return False
        key = dublf.shapeKeys.get_key(context)
        shape_keys = key.key_blocks
        num_keys = len(shape_keys)
        if num_keys == 0: return False
        active = obj.ska_active_index
        if active < 0: return False
        if active >= num_keys: return False
        return is_ska_key(shape_keys[active])

    def execute(self, context):
        obj = context.object
        obj.shape_key_remove(obj.data.shape_keys.key_blocks[obj.ska_active_index])
        return {'FINISHED'}

class DUSKA_UL_keys( bpy.types.UIList ):
    """The list of shape keys on an object"""
    bl_idname = "DUSKA_UL_keys"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if is_ska_key(item): layout.prop(item, 'name', text='', emboss=False, icon='SHAPEKEY_DATA')
        else: layout.label(text='Not animatable')

class DUSKA_PT_keys_control( bpy.types.Panel ):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Shape Keys animation"
    bl_idname = "DUSKA_PT_keys_controls"
    bl_category = 'Item'

    @classmethod
    def poll(self, context):
        obj = context.object
        return is_shape_keyable(obj)

    def draw(self, context):
        layout = self.layout
        obj = context.object
        key = obj.data.shape_keys
        if key is None:
            layout.operator("object.ska_add_key")
        else:
            row = layout.row()
            row.template_list("DUSKA_UL_keys", "", key , "key_blocks", obj , "ska_active_index" , rows = 3 )
            col = row.column(align=True)
            col.operator("object.ska_add_key", icon='ADD', text="")
            col.operator("object.ska_add_key", icon='PLUS', text="").from_mix = True
            col.operator("object.ska_remove_key", icon='REMOVE', text="")
        
classes = (
    DUSKA_OT_add_key,
    DUSKA_OT_remove_key,
    DUSKA_UL_keys,
    DUSKA_PT_keys_control,
)

def register():
    importlib.reload(dublf)
    importlib.reload(dublf.rigging)
    importlib.reload(dublf.shapeKeys)

    # register
    for cls in classes:
        bpy.utils.register_class(cls)

    if not hasattr( bpy.types.Object, 'ska_active_index' ):
        bpy.types.Object.ska_active_index = bpy.props.IntProperty( default=-1, update=view_ska_index, options={'ANIMATABLE','LIBRARY_EDITABLE'} )

    # Add handler
    dublf.handlers.frame_change_pre_append( update_keys_handler )
    
def unregister():
    # Remove handler
    dublf.handlers.frame_change_pre_remove( update_keys_handler )

    del bpy.types.Object.ska_active_index

    # unregister
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # modules
    # dublf.unregister()

if __name__ == "__main__":
    register()