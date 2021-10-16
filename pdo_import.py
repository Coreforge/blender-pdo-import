

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

        def decode(encoding, data):
            if encoding == 0:
                # *0x0e == 0 likely means utf-8 encoding
                return data.decode(encoding="utf-8")
            if encoding == 1:
                # *0x0e == 1 likely means utf-16 encoding
                return data.decode(encoding="utf-16")

        def skipDataBlockV6(f):
            #skips over the data Block in the header to the object count for format version 6

            # the number of Strings following? (though there is one more and one with 0 length, but after 2 bytes, there is another length and string, so idk)
            # ^ Wrong, seems to always be 3 Strings before weirdness
            # ^ They probably aren't strings but just some binary data (doesn't really matter anyways, it just needs to be skipped, which works)
            unknown_int_3 = int.from_bytes(f.read(4),byteorder='little')
            for x in range(3):
                data_len = int.from_bytes(f.read(4),byteorder='little')
                f.read(data_len) # advance to after the data block and just discard it (I don't know what it's for)
                print("Data Block %d length %d" % (x,data_len))

            # skip another block 
            f.read(2)   # advance by 2 bytes that contain some unknown data
            data_len = int.from_bytes(f.read(4),byteorder='little')
            f.read(data_len)
            f.read(0x24)    # skip another data block

        def skipDataBlockV5(f):
            f.read(4)   # skip over an unknown 32bit integer
            f.read(int.from_bytes(f.read(4),byteorder='little'))    # read size of first block and read first block
            f.read(int.from_bytes(f.read(4),byteorder='little'))    # read size of second block and read second block
            f.read(4)   # skip another unknown 32bit integer
            f.read(int.from_bytes(f.read(4),byteorder='little'))    # read size of third block and read third block
            f.read(0x22)    # skip another data block


        with open(self.filepath,"rb") as f:
            f.seek(0x0a)    # skip "version 3" string at the beginning

            # parse header

            # get some values from the header
            version = int.from_bytes(f.read(0x4),byteorder='little')
            encoding = int.from_bytes(f.read(4),byteorder='little')  # 0x0e, text encoding
            second_unknown_int = int.from_bytes(f.read(4),byteorder='little')   # 0x12
            text_length = int.from_bytes(f.read(4),byteorder='little')    # 0x16
            if encoding == 2:
                if version == 5:
                    self.report({"WARNING"},"File is weird. Header parsing is mostly based on fixed numbers, so high probability of it not working.")

                    f.read(0x12)    # skip a bunch of uint32s and 2 additional bytes I don't know what they're for
                    f.read(int.from_bytes(f.read(4),byteorder='little'))    # read size of data block and read the block
                    f.read(0x22)    # skip another data block (I don't know what it's for, but it has the same size as the block in the "normal" v5 files)
                else:
                    self.report({"ERROR"},"File is too weird. Please contact the author of the plugin.")
                    return  {"CANCELLED"}
            else:
                print("PDO File version: %d" % version)
                #print("second unknown int: %d" % second_unknown_int)

                # vendor String? (either "Pepakura Designer 4" or "Pepakura Designer 3")
                string_1 = decode(encoding,f.read(text_length))
                print("first String: %s" % string_1)

                if version == 6:
                    skipDataBlockV6(f)
                else :
                    skipDataBlockV5(f)


            num_objects = int.from_bytes(f.read(4),byteorder='little')
            f.read(int.from_bytes(f.read(4),byteorder='little'))    # read size of another block and read that block
            f.read(0x1)     # there is another byte after that block I don't know the purpose of, but I don't think it matters
            print(num_objects)
            
            for obj in range(1):    # only reading the first object because I don't know how to calculate the size of the last block yet
                fname = os.path.basename(f.name)

                # create the mesh, create an object, link the mesh to the object and link the object to the active collection of the current view layer
                mesh = bpy.data.meshes.new(fname[:len(fname) - 4])
                object = bpy.data.objects.new(fname[:len(fname) - 4],mesh)
                bpy.context.view_layer.active_layer_collection.collection.objects.link(object)

                # (currently hardcoded offset from the start of the file, needs to be changed once I figure out the block of data after the unfold data)
                num_verts = int.from_bytes(f.read(4),byteorder='little')
                print(num_verts)
                mesh.vertices.add(num_verts)
                
                for x in range(num_verts):
                    mesh.vertices[x].co = (struct.unpack("d",f.read(8))[0],struct.unpack("d",f.read(8))[0],struct.unpack("d",f.read(8))[0])
                
                num_faces = int.from_bytes(f.read(4),byteorder='little')
                print(num_faces)
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