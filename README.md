# Blender PDO Addon

An addon for blender to import pdo files from Pepakura 4 or Pepakura 3. Pepakura 3 files exported by Pepakura 4 may not work correctly as their header is different and the current code mostly uses fixed sizes to skip for these files.

Currently, only the first object in the file is imported, and the addon was only tested with Blender 2.93.
Also, only 3D model data is being imported, no textures or UVs.
