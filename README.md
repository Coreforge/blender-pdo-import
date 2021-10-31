# Blender PDO Addon

An addon for blender to import pdo files from Pepakura 4 or Pepakura 3. Pepakura 3 files exported by Pepakura 4 may not work correctly as their header is different and the current code mostly uses fixed sizes to skip for these files.

All objects in the file should now be imported. The addon has only been tested with blender 2.9, but it may work with blender 2.8 (I can't get that to run, so I can't test it). Blender 2.7 is incompatible.
Also, only 3D model data is being imported, no textures or UVs.
