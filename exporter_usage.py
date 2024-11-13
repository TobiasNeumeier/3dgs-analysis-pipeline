import sys

# Change this to the path where NerfSyntheticDatasetExporter is located
sys.path.append(r"C:\Users\danei\OneDrive\Uni\bachelor_thesis")

import bpy
from exporter import NerfSyntheticDatasetExporter
from pathlib import Path

# Change this to your center objects name in blender
center_object_name = "Sphere"
center_object = bpy.context.collection.objects[center_object_name]

# Change this to your export path where the dataset should be rendered to
export_path = Path(r"C:/Users/danei/OneDrive/Uni/bachelor_thesis/gaussian-splatting/data/test")

scene_exporter = NerfSyntheticDatasetExporter(bpy, export_path=export_path, focus_point=center_object, distance=10)

scene_exporter.render_all()
