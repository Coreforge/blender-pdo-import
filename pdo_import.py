

from posixpath import split
from bmesh.types import BMVert, BMesh
import bpy
import os
import struct
import bmesh
from bpy.types import MeshVertex

bl_info = {
    "name": "Pepakura PDO import",
    "blender": (2,90,0),
    "category": "Import/Export",
    "description": "Imports Pepakura 4 PDO files",
    "author": "Coreforge"
}

class ImportPDO(bpy.types.Operator):

    
    bl_idname = "import.pdo"
    bl_label = "Import .PDO"
    bl_description = "loads a pepakura 4 .pdo"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        print("Import PDO called")

        with open(self.filepath,"rb") as f:
            f.seek(0xce)    #   skip to the amount of objects
            num_objects = int.from_bytes(f.read(4),byteorder='little')
            for obj in range(1):    # only reading the first object because I don't know how to calculate the size of the last block yet
                fname = os.path.basename(f.name)

                # create the mesh, create an object, link the mesh to the object and link the object to the active collection of the current view layer
                mesh = bpy.data.meshes.new(fname[:len(fname) - 4])
                object = bpy.data.objects.new(fname[:len(fname) - 4],mesh)
                bpy.context.view_layer.active_layer_collection.collection.objects.link(object)

                f.seek(0xe1)    # go to where the number of verticies is stored as a uint32 (or int32)
                # (currently hardcoded offset from the start of the file, needs to be changed once I figure out the block of data after the unfold data)
                num_verts = int.from_bytes(f.read(4),byteorder='little')
                mesh.vertices.add(num_verts)
                
                for x in range(num_verts):
                    mesh.vertices[x].co = (struct.unpack("d",f.read(8))[0],struct.unpack("d",f.read(8))[0],struct.unpack("d",f.read(8))[0])
                
                num_faces = int.from_bytes(f.read(4),byteorder='little')
                edge_index = 0  # keeping track of the length of the edges array
                bm = bmesh.new()
                bm.from_mesh(mesh)
                for x in range(num_faces):
                    f.read(0x28)    # skip some per face data to the per vertex data
                    vertices = int.from_bytes(f.read(4),byteorder="little")
                    indicies = []   # declare list that holds the BMVerts for the current face
                    bm.verts.ensure_lookup_table()
                    for p in range(vertices):
                        indicies.append(bm.verts[int.from_bytes(f.read(4),byteorder="little")])
                        f.read(0x51)
                    bm.faces.ensure_lookup_table()
                    bm.faces.new(indicies)
                bm.to_mesh(mesh)
                bm.free()


        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def menu_func(self,context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator(ImportPDO.bl_idname,text="Pepakura 4 (.pdo)")

def register():
    print("loaded")
    bpy.utils.register_class(ImportPDO)
    bpy.types.TOPBAR_MT_file_import.append(menu_func)
    
def unregister():
    print("unloaded")
    bpy.utils.unregister_class(ImportPDO)

if __name__ == "__main__":
    register()