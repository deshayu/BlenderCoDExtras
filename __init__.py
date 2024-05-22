# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name" : "Blender Cod Tools Extras",
    "description" : "An addon that adds helpful scripts for working with CoD Assets in Blender",
    "author" : "deshayu_",
    "version" : (0, 1, 0),
    "blender" : (4, 10, 0),
    "location" : "View3D > N Panel/Properties > CoD Tools Extras",
    "warning" : "",
    "support" : "COMMUNITY",
    "doc_url" : "",
    "category" : "3D View"
}

import bpy
from bpy.props import BoolProperty

class CoDToolsExtrasProperties(bpy.types.PropertyGroup):

        merge_skeleton: bpy.props.BoolProperty(
        name="Merge Skeletons",
        description="Merge imported skeleton with the selected skeleton",
        default=False
    )

class CoDToolsExtras(bpy.types.Panel):
    bl_label = "CoD Tools Extras"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CoD Extras"

    @classmethod
    def poll(self,context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        codextratools = scene.def_codextratools

        # Animation Tools Row
        layout.label(text="Weapon Animation Tools:")
        
        row = layout.row()
        row.scale_y = 3.0
        row.operator("view3d.export_weapon_anim")
        
        row = layout.row()
        row.scale_y = 3.0
        row.operator("view3d.export_weapon_ads")
        
        # Weapon Tools Row
        layout.label(text="Weapon Tools:")
        
        row = layout.row()
        row.scale_y = 3.0
        row.operator("view3d.attach_weapon")

        row = layout.row(align=True)
        row.prop(codextratools, "merge_skeleton", icon='ARMATURE_DATA', text="Merge Skeletons")

class VIEW3D_Export_Weapon_ANIM(bpy.types.Operator):
    # Export Weapon Animation
    arg: bpy.props.StringProperty()
    bl_idname = "view3d.export_weapon_anim"
    bl_label = "Export"
    
    @classmethod
    def description(cls, context, properties):
        return "Export Animation" + properties.arg
    
    @classmethod
    def poll(cls, context):
        active_object = context.active_object
        return active_object is not None and active_object.type == 'ARMATURE' and (active_object.select_get())
    
    def execute(self, context):
        # Check if we're in Object mode or already in Pose
        checkmode(context)
        # Select All because blender hates hierarchy selection
        bpy.ops.pose.select_all(action='SELECT')
        # Disable for proper animation export
        bpy.context.object.data.bones['tag_view'].select = False
        bpy.context.object.data.bones['tag_ads'].select = False
        # Notify User
        self.report({'INFO'}, "Selected for Normal export")
    
        return {"FINISHED"}
        
class VIEW3D_Export_Weapon_ADS(bpy.types.Operator):
    # Export ADS Animation
    arg: bpy.props.StringProperty()
    bl_idname = "view3d.export_weapon_ads"
    bl_label = "Export ADS"
    
    @classmethod
    def description(cls, context, properties):
        return "Export ADS Animation" + properties.arg
    
    @classmethod
    def poll(cls, context):
        active_object = context.active_object   
        return active_object is not None and active_object.type == 'ARMATURE' and (active_object.select_get())
    
    def execute(self, context):
        # Check if we're in Object mode or already in Pose
        checkmode(context)
        # ADS only needs these 2
        bpy.context.object.data.bones['tag_view'].select = True
        bpy.context.object.data.bones['tag_torso'].select = True
        # Notify User
        self.report({'INFO'}, "Selected for ADS export")
    
        return {"FINISHED"}

class VIEW3D_Attach_Weapon(bpy.types.Operator):
    # Export ADS Animation
    arg: bpy.props.StringProperty()
    bl_idname = "view3d.attach_weapon"
    bl_label = "Attach Weapon"
    
    @classmethod
    def description(cls, context, properties):
        return "Attach Weapon to the Armature" + properties.arg
    
    @classmethod
    def poll(cls, context):
        active_object = context.active_object   
        return context.active_object.mode != 'POSE' and context.active_object.mode != 'EDIT' and active_object is not None and active_object.type == 'ARMATURE' and (active_object.select_get())
    
    def execute(self, context):
        # Find Hand Skeleton    
        skel_hands = find_arms(context)
        skel_weapon = find_weapon_arm(context)
        weapon_mesh = find_weapon_mesh(context)

        if skel_hands is not None and skel_weapon is not None:
            skel_weapon.parent = skel_hands
            if skel_weapon.pose.bones[0].name == "j_gun":
                skel_weapon.parent_bone = "tag_weapon"
            elif skel_weapon.pose.bones[0].name == "tag_weapon":
                    # Todo - add option to manually specify whether or not the user
                    #        wants to attach to the left or right hand
                skel_weapon.parent_bone = "tag_weapon_right"
            else:
                if skel_weapon.pose.bones[0].name in skel_hands.pose.bones:
                    skel_weapon.parent_bone = skel_weapon.pose.bones[0].name
                else:
                    print(("Warning: Armature '%s' may not" 
                            "merge correctly with '%s'") %
                            (skel_weapon.name, skel_hands.name))
                    skel_weapon.parent_bone = skel_hands.pose.bones[0].name
            skel_weapon.parent_type = 'BONE'
            skel_weapon.location = (0, -1, 0)

            # Is this necessary?
            bpy.context.view_layer.update()

            # Merge the skeletons together
            if bpy.context.scene.def_codextratools.merge_skeleton == True:
                join_armatures(skel_hands, skel_weapon, weapon_mesh)
            else:
                exit
            
            # Notify User
            self.report({'INFO'}, "Weapon Attached")
            return {"FINISHED"}
        self.report({'INFO'}, "Please select a Weapon Armature")
        return {"FINISHED"}

        

# Functions

def checkmode(context):
    if context.active_object.mode == 'POSE':
        bpy.ops.pose.select_all(action='DESELECT')
        exit
    else:
        bpy.ops.object.mode_set(mode='POSE')
        # Clear Selection
        bpy.ops.pose.select_all(action='DESELECT')

def find_arms(context):
    for ob in bpy.data.objects:
        if ob.type == 'ARMATURE' and ob.pose.bones[0].name == "tag_view":
            return ob

def find_weapon_arm(context):
    ob = context.active_object
    if ob.type == 'ARMATURE' and ob.pose.bones[0].name == "tag_weapon":
        return ob
    else:
        return None

def find_weapon_mesh(context):
    ob = context.active_object
    for obj in bpy.data.objects:
        if (obj.type == 'MESH' and ob in [m.object for m in obj.modifiers if m.type == 'ARMATURE']):
            return obj

def join_armatures(skel_hands_ob, skel_weapon_ob, weapon_mesh_ob):
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    # Select the armatures
    bpy.context.view_layer.objects.active = skel_hands_ob
    skel_hands_ob.select_set(state=True)
    bpy.ops.object.join()

    # Set the parent relationship
    combined_skeleton = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')  # Enter edit mode
    combined_skeleton.data.edit_bones['tag_weapon'].parent = combined_skeleton.data.edit_bones['tag_weapon_right']
    bpy.ops.object.mode_set(mode='OBJECT')  # Exit edit mode

    
    mesh_ob = weapon_mesh_ob
    # Remove any old armature modifiers
    if mesh_ob.modifiers:
        for modifier in mesh_ob.modifiers:
            if modifier.type == 'ARMATURE':
                mesh_ob.modifiers.remove(modifier)
    # Apply New armature modifier to the mesh
    modifier = mesh_ob.modifiers.new(name="Armature Rig", type="ARMATURE")
    modifier.object = combined_skeleton

# Register Classes

classes = (
    CoDToolsExtras,
    CoDToolsExtrasProperties,
    VIEW3D_Export_Weapon_ANIM,
    VIEW3D_Export_Weapon_ADS,
    VIEW3D_Attach_Weapon,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.def_codextratools = bpy.props.PointerProperty(type=CoDToolsExtrasProperties)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.def_codextratools


if __name__ == "__main__":
    register()