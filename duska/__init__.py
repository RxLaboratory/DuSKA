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
    "version": (1,1,0),
    "description": "Eases animation using shape keys (clay animation) and corrective shape keys.",
    "wiki_url": "https://duska-docs.rainboxlab.org/",
}

import bpy # pylint: disable=import-error
from bpy.app.handlers import persistent # pylint: disable=import-error
from statistics import mean

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
    # check if there are shape keys
    key = obj.data.shape_keys
    if key is None: return
    shape_keys = obj.data.shape_keys
    if shape_keys is None: return

    # set the right one
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

def getCurrentSka(obj, listIndex=0):
    """Returns the Current ska for the list"""
    active_index = getActiveSkaIndex(obj, listIndex)
    if active_index < 0: return None
    ska_keys = getattr(obj, 'ska_keys_' + str(listIndex))
    num_keys = len(ska_keys)
    if active_index >= num_keys: return None
    return ska_keys[active_index]

def getActiveSkaIndex(obj, listIndex=0):
    return getattr(obj, 'ska_active_index_' + str(listIndex))

def setActiveSka(obj, i, listIndex=0):
    setattr(obj, 'ska_active_index_'+str(listIndex), i)

def getSkaKeys(obj, listIndex=0):
    return getattr(obj, 'ska_keys_' + str(listIndex))

def update_ska_index(obj, context=bpy.context):
    """Updates the index of the Shape Key Animator"""
    if not is_shape_keyable(obj): return

    skavalues = [] # [ { 'ska':ska, 'values':[] }, ... ]

    def addToValues(ska, val):
        if val == 0: return
        for v in skavalues:
            if v['ska'].name == ska.name:
                v['values'].append(val)
                return

        values = []
        values.append(val)
        s = {
            'ska': ska,
            'values': values
        }
        skavalues.append( s )

    # if animated
    if dublf_animation.is_animated(obj):
        # for lists
        for i in range(0, 5):
            
            current_ska = getCurrentSka(obj, i)
            if not current_ska: continue
            
            ska_keys = getSkaKeys(obj, i)

            # get one or two values, add to skavalues
            curves = dublf_animation.get_curves(obj, 'ska_active_index_'+str(i))
            for fcurve in curves:
                frame = context.scene.frame_current
                # find keyframes
                keyframes = fcurve.keyframe_points
                # Juste one keyframe
                if len(keyframes) < 2:
                    addToValues(current_ska, 1.0)
                    continue
                # Get the previous key
                prev_key = dublf_animation.get_previous_keyframe(fcurve, frame)
                if prev_key is None:
                    addToValues(current_ska, 1.0)
                    continue
                prev_key_time = prev_key.co[0]
                prev_key_value = ska_keys[int(prev_key.co[1])]
                if prev_key.interpolation == 'CONSTANT':
                    addToValues(prev_key_value, 1.0)
                    continue
                # Interpolate
                next_key = dublf_animation.get_next_keyframe(fcurve, frame)
                if next_key is None:
                    addToValues(prev_key_value, 1.0)
                    continue
                next_key_time = next_key.co[0]
                next_key_value = ska_keys[int(next_key.co[1])]
                t = frame - prev_key_time
                d = next_key_time - prev_key_time
                if d == 0:
                    ratio = 1
                else:
                    ratio = t / d
                addToValues(prev_key_value, 1-ratio)
                addToValues(next_key_value, ratio)
    # not animated     
    else:
        # for lists
        for i in range(0, 5):
            current_ska = getCurrentSka(obj, i)
            addToValues(current_ska, 1)

    # Get the average for all skas
    skas = []
    values = []
    for v in skavalues:
        skas.append(v['ska'])
        values.append(mean(v['values']))
        set_ska_values(obj, skas, values)
            
def view_ska(obj, context, listIndex):
    current_ska = getCurrentSka(obj, listIndex)
    if not current_ska: return
    set_shape_key(obj, current_ska)

def view_ska_0(obj, context):
    view_ska(obj, context, 0)

def view_ska_1(obj, context):
    view_ska(obj, context, 1)

def view_ska_2(obj, context):
    view_ska(obj, context, 2)

def view_ska_3(obj, context):
    view_ska(obj, context, 3)

def view_ska_4(obj, context):
    view_ska(obj, context, 4)

def is_ska_key( sk, obj):
    # for lists
    for i in range(0, 5):
        ska_keys = getSkaKeys(obj, i)
        for ska in ska_keys:
            if ska.name == sk.name: return True
        return False

def has_corresponding_key( ska, obj ):
    # check if there are shape keys
    key = obj.data.shape_keys
    if key is None: return False

    # look for the right one
    for sk in obj.data.shape_keys.key_blocks:
        if sk.name == ska.name: return True
    return False

def rename_ska(self, name):
    if name == '': return
    obj = self.id_data

    sk = get_shape_key(obj, self)
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
    listIndex: bpy.props.IntProperty(default=0)

    @classmethod
    def poll(cls, context):
        obj = context.object
        return is_shape_keyable(obj)

    def execute(self, context):
        obj = context.object
        current_ska = getCurrentSka(obj, self.listIndex)
        if not current_ska: return {'CANCELLED'}
        current_ska_name = current_ska.name

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

    listIndex: bpy.props.IntProperty(default=0)

    @classmethod
    def poll(cls, context):
        obj = context.object
        if not is_shape_keyable(obj): return False
        if not obj.data.shape_keys: return False
        shape_keys = obj.data.shape_keys.key_blocks
        if len(shape_keys) == 0: return False
        return True

    def execute(self, context):
        obj = context.object

        shape_keys = obj.data.shape_keys.key_blocks
        active_shape_key = shape_keys[obj.active_shape_key_index]

        ska_keys = getSkaKeys(obj, self.listIndex)
        ska = ska_keys.add()
        ska.ska_name = active_shape_key.name

        return {'FINISHED'}

class DUSKA_OT_add_key( bpy.types.Operator ):
    bl_idname = "object.ska_add_key"
    bl_label = "New Animated Key"
    bl_description = "Creates a new Shape Key which will be used in the animation"
    bl_options = {'REGISTER','UNDO'}

    from_mix: bpy.props.BoolProperty(default=False)
    listIndex: bpy.props.IntProperty(default=0)

    @classmethod
    def poll(cls, context):
        obj = context.object
        return is_shape_keyable(obj)

    def execute(self, context):
        obj = context.object
        ska_keys = getSkaKeys(obj, self.listIndex)
        # Add a new key
        sk = obj.shape_key_add(name='SKA.Key', from_mix=self.from_mix)
        ska = ska_keys.add()
        ska.ska_name = sk.name
        shape_keys = obj.data.shape_keys.key_blocks
        num_keys = len(shape_keys)
        if num_keys == 1: # if it's the first, it's the basis
            sk.name = 'Basis'
            ska.ska_name = sk.name
            sk = obj.shape_key_add(name='SKA.Key', from_mix=False)
            ska = ska_keys.add()
            ska.ska_name = sk.name
        else: # let's check if the basis is there, if not add it
            create_basis = True
            basis_name = shape_keys[0].name
            for ska_key in ska_keys:
                if ska_key.name == basis_name:
                    create_basis = False
                    break
            if create_basis:
                ska_basis = ska_keys.add()
                ska_basis.ska_name = basis_name

        i = len(shape_keys)-1
        iSka = len(getSkaKeys(obj, self.listIndex)) -1
        obj.active_shape_key_index = i
        setActiveSka(obj, iSka, self.listIndex)

        # If autokey is active and there are keyframes, add a keyframe
        if context.tool_settings.use_keyframe_insert_auto:
            curves = dublf_animation.get_curves(obj, 'ska_active_index_'+str(self.listIndex))
            for curve in curves:
                keyframes = curve.keyframe_points
                if len(keyframes) > 0:
                    keyframes.insert(context.scene.frame_current, iSka)
        
        return {'FINISHED'}

class DUSKA_OT_remove_key(bpy.types.Operator ):
    bl_idname = "object.ska_remove_key"
    bl_label = "Remove Key"
    bl_description = "Removes a new Shape Key to be used in the animation"
    bl_options = {'REGISTER','UNDO'}

    delete: bpy.props.BoolProperty(default=False)
    listIndex: bpy.props.IntProperty(default=0)

    @classmethod
    def poll(cls, context):
        obj = context.object
        return is_shape_keyable(obj)

    def execute(self, context):
        obj = context.object
        current_ska = getCurrentSka(obj, self.listIndex)
        if not current_ska: return {'CANCELLED'}

        # remove all keyframes referencing this ska
        # and adjust values of other keyframes to continue referencing the right skas
        active_index = getActiveSkaIndex(obj, self.listIndex)
        dublf_animation.remove_animated_index(obj, 'ska_active_index_'+str(self.listIndex), active_index )

        if not obj.data.shape_keys:
            self.delete = False

        if self.delete:
            shape_key = get_shape_key(obj, getCurrentSka(obj, self.listIndex))
            shape_keys = obj.data.shape_keys.key_blocks
            if shape_key is not None:
                if shape_key.name != shape_keys[0].name: # Do not delete basis
                    obj.shape_key_remove( shape_key )
        ska_keys = getSkaKeys(obj, self.listIndex)
        ska_keys.remove( getActiveSkaIndex(obj, self.listIndex) )
        return {'FINISHED'}

class DUSKA_OT_move_ska( bpy.types.Operator ):
    bl_idname = "object.ska_move_key"
    bl_label = "Move Key"
    bl_description = "Moves a Shape Key in the list"
    bl_options = {'REGISTER','UNDO'}

    up: bpy.props.BoolProperty(default = True)
    listIndex: bpy.props.IntProperty(default=0)

    @classmethod
    def poll(cls, context):
        obj = context.object
        return is_shape_keyable(obj)

    def execute(self, context):
        obj = context.object
        current_ska = getCurrentSka(obj, self.listIndex)
        if not current_ska: return {'CANCELLED'}

        current_index = getActiveSkaIndex(obj, self.listIndex)
        skas = getSkaKeys(obj, self.listIndex)

        if self.up and current_index <= 0: return {'CANCELLED'}
        if not self.up and current_index >= len(skas) -1: return {'CANCELLED'}

        new_index = 0
        if self.up: new_index = current_index - 1
        else: new_index = current_index + 1

        # update keyframes values
        dublf_animation.swap_animated_index(obj, 'ska_active_index_'+str(self.listIndex), current_index, new_index)

        skas.move(current_index, new_index)
        setActiveSka(obj, new_index, self.listIndex)

        return {'FINISHED'}

class DUSKA_OT_delete_all_keys( bpy.types.Operator ):
    bl_idname = "object.ska_delete_all"
    bl_label = "Delete all Animated Keys"
    bl_description = "Removes all shape keys from the animation"
    bl_options = {'REGISTER','UNDO'}

    delete: bpy.props.BoolProperty(default=False)
    listIndex: bpy.props.IntProperty(default=0)

    @classmethod
    def poll(cls, context):
        obj = context.object
        return is_shape_keyable(obj)

    def execute(self, context):
        obj = context.object

        # remove all keyframes animation
        dublf_animation.remove_all_keyframes(obj, 'ska_active_index_'+str(self.listIndex) )

        if not obj.data.shape_keys:
            self.delete = False
        else:
            shape_keys = obj.data.shape_keys.key_blocks

        ska_keys = getSkaKeys(obj, self. listIndex)
        while len(ska_keys) > 0:
            if self.delete:
                shape_key = get_shape_key(obj, ska_keys[0])
                if shape_key is not None:
                    if shape_key.name != shape_keys[0].name: # Do not delete basis
                        obj.shape_key_remove( shape_key )
            ska_keys.remove( 0 )

        return {'FINISHED'}

def draw_menu(layout, listIndex):
    op = layout.operator("object.ska_add_key", icon='ADD', text="New Animated Key")
    op.from_mix = False
    op.listIndex = listIndex
    op = layout.operator("object.ska_add_key", icon='ADD', text="New Animated Key from mix")
    op.from_mix = True
    op.listIndex = listIndex
    layout.separator()
    op = layout.operator("object.ska_include_key", icon='ADD', text="Add active Shape Key to animation")
    op.listIndex = listIndex
    layout.separator()
    op = layout.operator("object.ska_remove_key", icon='REMOVE', text="Remove Animated Key from animation")
    op.delete = False
    op.listIndex = listIndex
    op = layout.operator("object.ska_remove_key", icon='X', text="Delete Shape Key")
    op.delete = True
    op.listIndex = listIndex
    layout.separator()
    op = layout.operator("object.ska_delete_all", icon='REMOVE', text="Remove All Animated Keys from animation")
    op.delete = False
    op.listIndex = listIndex
    op = layout.operator("object.ska_delete_all", icon='X', text="Delete All Shape Keys")
    op.delete = True
    op.listIndex = listIndex

class DUSKA_MT_menu0( bpy.types.Menu ):
    bl_label = 'SKA'
    bl_idname = 'DUSKA_MT_menu0'

    def draw(self, context):
        layout = self.layout
        draw_menu(layout, 0)
            
class DUSKA_MT_menu1( bpy.types.Menu ):
    bl_label = 'SKA'
    bl_idname = 'DUSKA_MT_menu1'

    def draw(self, context):
        layout = self.layout
        draw_menu(layout, 1)

class DUSKA_MT_menu2( bpy.types.Menu ):
    bl_label = 'SKA'
    bl_idname = 'DUSKA_MT_menu2'

    def draw(self, context):
        layout = self.layout
        draw_menu(layout, 2)

class DUSKA_MT_menu3( bpy.types.Menu ):
    bl_label = 'SKA'
    bl_idname = 'DUSKA_MT_menu3'

    def draw(self, context):
        layout = self.layout
        draw_menu(layout, 3)

class DUSKA_MT_menu4( bpy.types.Menu ):
    bl_label = 'SKA'
    bl_idname = 'DUSKA_MT_menu4'

    def draw(self, context):
        layout = self.layout
        draw_menu(layout, 4)

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

        first_empty_list = -1

        for i in range(0,5):
            num_keys = len(getSkaKeys(obj, i))
            if num_keys == 0:
                if first_empty_list == -1:
                    first_empty_list = i
                continue
            row = layout.row()
            row.template_list("DUSKA_UL_keys", "", obj , "ska_keys_"+str(i), obj , "ska_active_index_"+str(i) , rows = 3 )
            col = row.column(align=True)
            op = col.operator("object.ska_add_key", icon='ADD', text="")
            op.from_mix = True
            op.listIndex = i
            op = col.operator("object.ska_edit_key", icon='EDITMODE_HLT', text="")
            op.sculpt = False
            op.listIndex = i
            op = col.operator("object.ska_edit_key", icon='SCULPTMODE_HLT', text="")
            op.sculpt = True
            op.listIndex = i
            col.separator()
            col.menu("DUSKA_MT_menu"+str(i), icon='DOWNARROW_HLT', text="")
            col.separator()
            op = col.operator('object.ska_move_key',  icon='TRIA_UP', text="")
            op.up = True
            op.listIndex = i
            op = col.operator('object.ska_move_key',  icon='TRIA_DOWN', text="")
            op.up = False
            op.listIndex = i
        
        if first_empty_list > -1:
            row = layout.row()
            op = row.operator("object.ska_add_key", icon='ADD', text="New animated key group")
            op.from_mix = True
            op.listIndex = first_empty_list
        
classes = (
    DUSKA_key,
    DUSKA_OT_edit,
    DUSKA_OT_include_key,
    DUSKA_OT_add_key,
    DUSKA_OT_remove_key,
    DUSKA_OT_move_ska,
    DUSKA_OT_delete_all_keys,
    DUSKA_MT_menu0,
    DUSKA_MT_menu1,
    DUSKA_MT_menu2,
    DUSKA_MT_menu3,
    DUSKA_MT_menu4,
    DUSKA_UL_keys,
    DUSKA_PT_keys_control,
)

def register():
    # register
    for cls in classes:
        bpy.utils.register_class(cls)

    if not hasattr( bpy.types.Object, 'ska_active_index_0'):
        bpy.types.Object.ska_active_index_0 = bpy.props.IntProperty( default=-1, update=view_ska_0, options={'ANIMATABLE','LIBRARY_EDITABLE'} )
    if not hasattr( bpy.types.Object, 'ska_keys_0'):
        bpy.types.Object.ska_keys_0 = bpy.props.CollectionProperty( type=DUSKA_key )
    if not hasattr( bpy.types.Object, 'ska_active_index_1'):
        bpy.types.Object.ska_active_index_1 = bpy.props.IntProperty( default=-1, update=view_ska_1, options={'ANIMATABLE','LIBRARY_EDITABLE'} )
    if not hasattr( bpy.types.Object, 'ska_keys_1'):
        bpy.types.Object.ska_keys_1 = bpy.props.CollectionProperty( type=DUSKA_key )
    if not hasattr( bpy.types.Object, 'ska_active_index_2'):
        bpy.types.Object.ska_active_index_2 = bpy.props.IntProperty( default=-1, update=view_ska_2, options={'ANIMATABLE','LIBRARY_EDITABLE'} )
    if not hasattr( bpy.types.Object, 'ska_keys_2'):
        bpy.types.Object.ska_keys_2 = bpy.props.CollectionProperty( type=DUSKA_key )
    if not hasattr( bpy.types.Object, 'ska_active_index_3'):
        bpy.types.Object.ska_active_index_3 = bpy.props.IntProperty( default=-1, update=view_ska_3, options={'ANIMATABLE','LIBRARY_EDITABLE'} )
    if not hasattr( bpy.types.Object, 'ska_keys_3'):
        bpy.types.Object.ska_keys_3 = bpy.props.CollectionProperty( type=DUSKA_key )
    if not hasattr( bpy.types.Object, 'ska_active_index_4'):
        bpy.types.Object.ska_active_index_4 = bpy.props.IntProperty( default=-1, update=view_ska_4, options={'ANIMATABLE','LIBRARY_EDITABLE'} )
    if not hasattr( bpy.types.Object, 'ska_keys_4'):
        bpy.types.Object.ska_keys_4 = bpy.props.CollectionProperty( type=DUSKA_key )

    # Add handler
    dublf_handlers.frame_change_pre_append( update_keys_handler )
    
def unregister():
    # Remove handler
    dublf_handlers.frame_change_pre_remove( update_keys_handler )

    del bpy.types.Object.ska_keys_0
    del bpy.types.Object.ska_active_index_0
    del bpy.types.Object.ska_keys_1
    del bpy.types.Object.ska_active_index_1
    del bpy.types.Object.ska_keys_2
    del bpy.types.Object.ska_active_index_2
    del bpy.types.Object.ska_keys_3
    del bpy.types.Object.ska_active_index_3
    del bpy.types.Object.ska_keys_4
    del bpy.types.Object.ska_active_index_4

    # unregister
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # modules
    # dublf.unregister()

if __name__ == "__main__":
    register()