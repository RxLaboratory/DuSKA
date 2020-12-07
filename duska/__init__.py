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
    "location": "3D View ▸ Sidebar ▸ Item",
    "version": (1,0,0),
    "description": "Eases animation using shape keys (clay animation) and corrective shape keys.",
    "wiki_url": "https://duska-docs.rainboxlab.org/",
}

import bpy # pylint: disable=import-error
from bpy.app.handlers import persistent # pylint: disable=import-error

from .dublf import handlers as dublf_handlers # pylint: disable=import-error
from .dublf import animation as dublf_animation # pylint: disable=import-error

def is_shape_keyable(obj):
    if obj is None: return False
    return obj.type == 'CURVE' or obj.type == 'MESH'

def get_shape_key(obj, ska):
    shape_keys = obj.data.shape_keys
    if shape_keys is None: return
    for sk in shape_keys.key_blocks:
        if not has_corresponding_key(sk, obj): continue
        if ska.name == sk.name: return sk
    return None

def set_shape_key(obj, ska):
    shape_keys = obj.data.shape_keys
    if shape_keys is None: return
    for sk in shape_keys.key_blocks:
        if not is_ska_key(sk, obj): continue
        if ska.name == sk.name:
            sk.value = 1
        else:
            sk.value = 0

def set_ska_values(obj, skas, values):
    shape_keys = obj.data.shape_keys
    if shape_keys is None: return

    for i, ska in enumerate(skas):
        for sk in shape_keys.key_blocks:
            if sk.name == ska.name:     
                sk.value = values[i]

    for i, sk in enumerate(shape_keys.key_blocks):
        if not is_ska_key(sk, obj): continue
        ok = True
        for ska in skas:
            if sk.name == ska.name:
                ok = False
                break
        if ok:
            sk.value = 0

def update_ska_index(obj, context=bpy.context):
    """Updates the index of the Shape Key Animator"""
    if not is_shape_keyable(obj): return

    active_index = obj.ska_active_index
    if active_index < 0: return
    num_keys = len(obj.ska_keys)
    if active_index >= num_keys: return

    current_ska = obj.ska_keys[active_index]
    
    # check if the index is animated, if so interpolate
    if dublf_animation.is_animated(obj):
        curves = dublf_animation.get_curves(obj, 'ska_active_index')
        for fcurve in curves:
            frame = context.scene.frame_current
            # find keyframes
            keyframes = fcurve.keyframe_points
            # Juste one keyframe
            if len(keyframes) < 2:
                set_shape_key(obj, current_ska)
                return
            # Get the previous key
            prev_key = dublf_animation.get_previous_keyframe(fcurve, frame)
            if prev_key is None:
                set_shape_key(obj, current_ska)
                return
            prev_key_time = prev_key.co[0]
            prev_key_value = obj.ska_keys[int(prev_key.co[1])]
            if prev_key.interpolation == 'CONSTANT':
                set_shape_key(obj, prev_key.co[1])
                return
            # Interpolate
            next_key = dublf_animation.get_next_keyframe(fcurve, frame)
            if next_key is None:
                set_shape_key(obj, prev_key_value)
                return
            next_key_time = next_key.co[0]
            next_key_value = obj.ska_keys[int(next_key.co[1])]
            t = frame - prev_key_time
            d = next_key_time - prev_key_time
            if d == 0:
                ratio = 1
            else:
                ratio = t / d
            set_ska_values(obj, [ prev_key_value, next_key_value ], [ 1-ratio, ratio ])
    else:
        set_shape_key(obj, current_ska)
        
def view_ska(obj, context):
    key = obj.data.shape_keys
    if key is None: return
    current_index = obj.ska_active_index
    if current_index < 0: return
    if current_index >= len(obj.ska_keys): return
    current_key = obj.ska_keys[current_index]
    set_shape_key(obj, current_key)

def is_ska_key( sk, obj):
    for ska in obj.ska_keys:
        if ska.name == sk.name: return True
    return False

def has_corresponding_key( ska, obj ):
    key = obj.data.shape_keys
    if key is None: return False
    for sk in obj.data.shape_keys.key_blocks:
        if sk.name == ska.name: return True
    return False

def rename_ska(self, name):
    if name == '': return
    obj = self.id_data
    ska = obj.ska_keys[obj.ska_active_index]
    sk = get_shape_key(obj, ska)
    if sk is not None:
        sk.name = name
    self.ska_name = name

def ska_name(self):
    return self.ska_name

@persistent
def update_keys_handler( scene ):
    """Updates all keys"""
    for obj in bpy.data.objects:
        update_ska_index(obj, bpy.context)

class DUSKA_key( bpy.types.PropertyGroup ):
    name: bpy.props.StringProperty( default="SKA.key", set=rename_ska, get=ska_name )
    ska_name:bpy.props.StringProperty()

class DUSKA_OT_edit( bpy.types.Operator ):
    bl_idname = "object.ska_edit_key"
    bl_label = "Edit Animated Key"
    bl_description = "Edits the selected Animated Key"
    bl_options = {'REGISTER','UNDO'}

    sculpt: bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        obj = context.object
        num_keys = len(obj.ska_keys)
        if num_keys == 0: return False
        if obj.ska_active_index < 0: return False
        if obj.ska_active_index >= num_keys: return False
        return True

    def execute(self, context):
        obj = context.object
        current_ska_name = obj.ska_keys[obj.ska_active_index].name
        ok = False
        for i, s in enumerate(obj.data.shape_keys.key_blocks):
            if s.name == current_ska_name:
                obj.active_shape_key_index = i
                ok = True
                break
        if ok:
            if self.sculpt:
                bpy.ops.object.mode_set(mode='SCULPT')
            else:
                bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}

class DUSKA_OT_include_key( bpy.types.Operator ):
    bl_idname = "object.ska_include_key"
    bl_label = "Add Key to animation"
    bl_description = "Includes a new Shape Key to be used in the animation"
    bl_options = {'REGISTER','UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        if not is_shape_keyable(obj): return False
        shape_keys = obj.data.shape_keys.key_blocks
        active_shape_key = shape_keys[obj.active_shape_key_index]
        for ska in obj.ska_keys:
            if ska.name == active_shape_key.name: return False
        return True

    def execute(self, context):
        obj = context.object

        shape_keys = obj.data.shape_keys.key_blocks
        active_shape_key = shape_keys[obj.active_shape_key_index]

        ska = obj.ska_keys.add()
        ska.ska_name = active_shape_key.name

        return {'FINISHED'}

class DUSKA_OT_add_key( bpy.types.Operator ):
    bl_idname = "object.ska_add_key"
    bl_label = "New Animated Key"
    bl_description = "Creates a new Shape Key which will be used in the animation"
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
        ska = obj.ska_keys.add()
        ska.ska_name = sk.name
        shape_keys = obj.data.shape_keys.key_blocks
        num_keys = len(shape_keys)
        if num_keys == 1: # if it's the first, it's the basis
            sk.name = 'Basis'
            ska.ska_name = sk.name
            sk = obj.shape_key_add(name='SKA.Key', from_mix=False)
            ska = obj.ska_keys.add()
            ska.ska_name = sk.name
        else: # let's check if the basis is there, if not add it
            create_basis = True
            basis_name = shape_keys[0].name
            for ska_key in obj.ska_keys:
                if ska_key.name == basis_name:
                    create_basis = False
                    break
            if create_basis:
                ska_basis = obj.ska_keys.add()
                ska_basis.ska_name = basis_name

        i = len(shape_keys)-1
        obj.active_shape_key_index = i
        obj.ska_active_index = i

        # If autokey is active and there are keyframes, add a keyframe
        if context.tool_settings.use_keyframe_insert_auto:
            curves = dublf_animation.get_curves(obj, 'ska_active_index')
            for curve in curves:
                keyframes = curve.keyframe_points
                if len(keyframes) > 0:
                    keyframes.insert(context.scene.frame_current, obj.ska_active_index)
        
        return {'FINISHED'}

class DUSKA_OT_remove_key(bpy.types.Operator ):
    bl_idname = "object.ska_remove_key"
    bl_label = "Remove Key"
    bl_description = "Removes a new Shape Key to be used in the animation"
    bl_options = {'REGISTER','UNDO'}

    delete: bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        obj = context.object
        num_keys = len(obj.ska_keys)
        if num_keys == 0: return False
        if obj.ska_active_index < 0: return False
        if obj.ska_active_index >= num_keys: return False
        return True

    def execute(self, context):
        obj = context.object

        # remove all keyframes referencing this ska
        # and adjust values of other keyframes to continue referencing the right skas
        dublf_animation.remove_animated_index(obj, 'ska_active_index', obj.ska_active_index)

        if self.delete:
            shape_key = get_shape_key(obj, obj.ska_keys[obj.ska_active_index])
            if shape_key is not None:
                obj.shape_key_remove( shape_key )
        obj.ska_keys.remove( obj.ska_active_index )
        return {'FINISHED'}

class DUSKA_OT_move_ska( bpy.types.Operator ):
    bl_idname = "object.ska_move_key"
    bl_label = "Move Key"
    bl_description = "Moves a Shape Key in the list"
    bl_options = {'REGISTER','UNDO'}

    up: bpy.props.BoolProperty(default = True)

    @classmethod
    def poll(cls, context):
        obj = context.object
        num_keys = len(obj.ska_keys)
        if num_keys < 2: return False
        if obj.ska_active_index < 0: return False
        if obj.ska_active_index >= num_keys: return False
        return True

    def execute(self, context):
        obj = context.object
        current_index = obj.ska_active_index
        skas = obj.ska_keys

        if self.up and current_index <= 0: return {'CANCELLED'}
        if not self.up and current_index >= len(skas) -1: return {'CANCELLED'}

        new_index = 0
        if self.up: new_index = current_index - 1
        else: new_index = current_index + 1

        # update keyframes values
        dublf_animation.swap_animated_index(obj, 'ska_active_index', current_index, new_index)

        skas.move(current_index, new_index)
        obj.ska_active_index = new_index

        return {'FINISHED'}

class DUSKA_MT_menu( bpy.types.Menu ):
    bl_label = 'SKA'
    bl_idname = 'DUSKA_MT_menu'

    def draw(self, context):
        layout = self.layout
        layout.operator("object.ska_add_key", icon='ADD', text="New Animated Key").from_mix = False
        layout.operator("object.ska_add_key", icon='ADD', text="New Animated Key from mix").from_mix = True
        layout.separator()
        layout.operator("object.ska_include_key", icon='ADD', text="Add active Shape Key to animation")
        layout.separator()
        layout.operator("object.ska_remove_key", icon='REMOVE', text="Remove Animated Key from animation").delete = False
        layout.operator("object.ska_remove_key", icon='X', text="Delete Shape Key").delete = True

class DUSKA_UL_keys( bpy.types.UIList ):
    """The list of shape keys on an object"""
    bl_idname = "DUSKA_UL_keys"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if has_corresponding_key(item, data):
            obj = context.object
            i = 'SHAPEKEY_DATA'
            if obj.data.shape_keys.key_blocks[0].name == item.name:
                i = 'MESH_DATA'
            layout.prop(item, 'name', text='', emboss=False, icon=i)
        else:
            layout.prop(item, 'name', text='', emboss=False, icon='ERROR')

class DUSKA_PT_keys_control( bpy.types.Panel ):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Shape Keys Animation"
    bl_idname = "DUSKA_PT_keys_controls"
    bl_category = 'Item'

    @classmethod
    def poll(self, context):
        obj = context.object
        return is_shape_keyable(obj)

    def draw(self, context):
        layout = self.layout
        obj = context.object
        num_keys = len(obj.ska_keys)
        if num_keys == 0:
            layout.operator("object.ska_add_key")
        else:
            row = layout.row()
            row.template_list("DUSKA_UL_keys", "", obj , "ska_keys", obj , "ska_active_index" , rows = 3 )
            col = row.column(align=True)
            col.operator("object.ska_add_key", icon='ADD', text="").from_mix = True
            col.operator("object.ska_edit_key", icon='EDITMODE_HLT', text="").sculpt = False
            col.operator("object.ska_edit_key", icon='SCULPTMODE_HLT', text="").sculpt = True
            col.separator()
            col.menu("DUSKA_MT_menu", icon='DOWNARROW_HLT', text="")
            col.separator()
            col.operator('object.ska_move_key',  icon='TRIA_UP', text="").up = True
            col.operator('object.ska_move_key',  icon='TRIA_DOWN', text="").up = False
        
classes = (
    DUSKA_key,
    DUSKA_OT_edit,
    DUSKA_OT_include_key,
    DUSKA_OT_add_key,
    DUSKA_OT_remove_key,
    DUSKA_OT_move_ska,
    DUSKA_MT_menu,
    DUSKA_UL_keys,
    DUSKA_PT_keys_control,
)

def register():
    # register
    for cls in classes:
        bpy.utils.register_class(cls)

    if not hasattr( bpy.types.Object, 'ska_active_index' ):
        bpy.types.Object.ska_active_index = bpy.props.IntProperty( default=-1, update=view_ska, options={'ANIMATABLE','LIBRARY_EDITABLE'} )
    if not hasattr( bpy.types.Object, 'ska_keys'):
        bpy.types.Object.ska_keys = bpy.props.CollectionProperty( type=DUSKA_key )

    # Add handler
    dublf_handlers.frame_change_pre_append( update_keys_handler )
    
def unregister():
    # Remove handler
    dublf_handlers.frame_change_pre_remove( update_keys_handler )

    del bpy.types.Object.ska_keys
    del bpy.types.Object.ska_active_index

    # unregister
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # modules
    # dublf.unregister()

if __name__ == "__main__":
    register()