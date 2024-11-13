import os
import math
import json
import random
import shutil
from pathlib import Path


def point_camera_at(camera, target):
    # Compute the direction vector from camera to target
    direction = target.location - camera.location
    
    # Create a rotation that points the camera's -Z axis along the direction vector
    # and keeps the Y axis pointing upwards to avoid roll
    rot_quat = direction.to_track_quat('-Z', 'Y')
    
    # Apply the rotation to the camera
    camera.rotation_euler = rot_quat.to_euler()
    
    # Ensure the rotation mode is set to 'XYZ' (default)
    camera.rotation_mode = 'XYZ'


# Function to get the camera's transformation (view) matrix
def get_camera_transform_matrix(_scene):
    _camera = _scene.camera
    # Get the 4x4 transformation matrix (world to camera space)
    M = _camera.matrix_local
    return [list(row) for row in M]  # Convert to list of lists for easier handling


class NerfSyntheticDatasetExporter:

    def __init__(self, bpy, export_path: Path, focus_point, distance, dataset_sizes=None):
        self.set_and_create_export_path(export_path=export_path)
        if not dataset_sizes:
            dataset_sizes = {
                "train": 100,
                "val": 100,
                "test": 200
            }
        self.dataset_sizes = dataset_sizes
        self.scene = bpy.context.scene
        self.context = bpy.context
        self.data = bpy.data
        self.ops = bpy.ops
        
        self.focus_point = focus_point
        self.distance_from_focus = distance

        # Initialize the camera object
        camera_data = self.data.cameras.new("Camera")
        self.camera = self.data.objects.new("Camera", camera_data)
        self.scene.collection.objects.link(self.camera)
        self.context.scene.camera = self.camera

        print(f"Initialized scene: {self.scene}; type <{type(self.scene)}>")

        # Initialize the camera positions list
        self.randomize_camera_locations()

        self.log_str = ""

    def set_and_create_export_path(self, export_path):
        self.export_path = export_path
        print(f"Set export path: {self.export_path}")
        train_dir = self.export_path / "train"
        val_dir = self.export_path / "val"
        test_dir = self.export_path / "test"
        
        if os.path.exists(export_path):
            # delete existing directory
            shutil.rmtree(export_path)
            print(f"Deleted existing export path: {export_path}")
        
        # Make dirs
        os.makedirs(self.export_path, exist_ok=True)
        os.makedirs(train_dir, exist_ok=True)
        os.makedirs(test_dir, exist_ok=True)
        os.makedirs(val_dir, exist_ok=True)
        print("Export directory created.")

    def randomize_camera_locations(self):
        """
        Randomizes camera positions around a focus_point object in spherical coordinates, 
        while ensuring that the camera remains at a fixed distance from the focus point.

        Parameters:
        focus_point: The object around which the camera should be positioned. 
                     It is expected to have a 'location' attribute (e.g., a Blender object).
        distance: The fixed distance from the camera to the focus point (default is 7 units).
        """

        # Extract the focus point's coordinates
        focus_x, focus_y, focus_z = self.focus_point.location

        # Clear the camera positions list
        self.camera_positions = []

        total_number_of_frames = sum(self.dataset_sizes.values())

        for _ in range(total_number_of_frames):
            # Randomize the spherical coordinates for the camera
            # theta is the horizontal angle (0 to 360 degrees)
            # phi is the vertical angle (20 to 160 degrees, to avoid extreme top or bottom views)
            theta = random.uniform(0, 2 * math.pi)  # Random angle around the focus point (horizontal)
            phi = random.uniform(math.radians(20), math.radians(160))  # Random angle for elevation

            # Convert spherical coordinates to cartesian (x, y, z)
            camera_x = self.distance_from_focus * math.sin(phi) * math.cos(theta) + focus_x
            camera_y = self.distance_from_focus * math.sin(phi) * math.sin(theta) + focus_y
            camera_z = self.distance_from_focus * math.cos(phi) + focus_z

            # Append the new camera position relative to the focus point
            self.camera_positions.append((camera_x, camera_y, camera_z))

    def prepare_frame(self, frame_number):
        """
        Moves the camera to a new position and aligns it to look at the focus point.

        Parameters:
        frame_number: The frame number to set in the scene.
        focus_point: The object to look at (e.g., a Blender object).
        """
        # Load and set camera position
        camera_x, camera_y, camera_z = self.camera_positions[frame_number]
        self.camera.location = (camera_x, camera_y, camera_z)
        
        # Point the camera at the focus point
        point_camera_at(self.camera, self.focus_point)

    @property
    def current_camera_transform_matrix(self):
        # Get the 4x4 transformation matrix (world to camera space)
        M = self.scene.camera.matrix_local
        return [list(row) for row in M] 

    def print_info(self, message):
        self.ops.wm.report({'INFO'}, message)

    def log(self, message):
        """
        Logs a message to the exporter's log.
        """
        self.log_str += message + "\n"

    def write_log(self):
        """
        Writes the exporter's log to a file.
        """
        log_file_path = f"{self.export_path}/exporter_log.txt"
    
        with open(log_file_path, "w") as f:
            f.write(self.log_str)
            f.close()

    def test_render(self):
        """
        Use this to test rendering a single frame to ensure the output is as desired.
        """

        # Set the rendering engine to Cycles
        self.context.scene.render.engine = 'CYCLES'

        # Enable GPU rendering for the scene in Cycles settings
        self.context.scene.cycles.device = 'GPU'

        # Optional: Configure the number of samples for rendering (affects render quality)
        self.context.scene.cycles.samples = 128  # Adjust sample size

        preferences = self.context.preferences.addons['cycles'].preferences
        preferences.compute_device_type = 'CUDA'  # For NVIDIA, change to 'OPENCL' for AMD
        preferences.get_devices()  # Make sure devices are detected

        # Set the active GPU device
        self.context.scene.cycles.device = 'GPU'

        self.context.scene.render.image_settings.file_format = 'PNG'
        self.context.scene.render.resolution_x = 960
        self.context.scene.render.resolution_y = 540
        self.context.scene.render.image_settings.color_mode = 'RGB'
        self.context.scene.render.image_settings.color_depth = '16'
        self.context.scene.render.image_settings.compression = 15
        self.context.scene.render.image_settings.color_depth = '16'

        def render_image(filepath):
            self.log(f"Rendering image to: {filepath}")  # Debugging
            self.scene.render.filepath = str(filepath)
            self.ops.render.render(write_still=True)


        # Render all frames for each dataset type
        self.prepare_frame(0)
        image_path = self.export_path / "test.png"
        # Render the image
        render_image(image_path)
        
    def render_all(self):
        """
        Renders all frames for the training, validation, and test sets.
        Also saves the camera positions as json files.
        """

        # Set the rendering engine to Cycles
        self.context.scene.render.engine = 'CYCLES'

        # Enable GPU rendering for the scene in Cycles settings
        self.context.scene.cycles.device = 'GPU'

        # Optional: Configure the number of samples for rendering (affects render quality)
        self.context.scene.cycles.samples = 128  # Adjust sample size

        preferences = self.context.preferences.addons['cycles'].preferences
        preferences.compute_device_type = 'CUDA'  # For NVIDIA, change to 'OPENCL' for AMD
        preferences.get_devices()  # Make sure devices are detected

        # Set the active GPU device
        self.context.scene.cycles.device = 'GPU'

        self.context.scene.render.image_settings.file_format = 'PNG'
        self.context.scene.render.resolution_x = 960
        self.context.scene.render.resolution_y = 540
        self.context.scene.render.image_settings.color_mode = 'RGB'
        self.context.scene.render.image_settings.color_depth = '16'
        self.context.scene.render.image_settings.compression = 15
        self.context.scene.render.image_settings.color_depth = '16'

        def render_image(filepath):
            self.log(f"Rendering image to: {filepath}")  # Debugging
            self.scene.render.filepath = str(filepath)
            self.ops.render.render(write_still=True)

        # Dictionaries to store the camera transforms for each set
        transforms_dicts = {
            "train": {
                "camera_angle_x": self.scene.camera.data.angle_x,
                "frames": []
            },
            "val": {
                "camera_angle_x": self.scene.camera.data.angle_x,
                "frames": []
            },
            "test": {
                "camera_angle_x": self.scene.camera.data.angle_x,
                "frames": []
            }
        }

        # Render all frames for each dataset type
        c_frame = 0
        self.log(f"Rendering frames to {self.export_path}")
        for dataset_type, n_frames in self.dataset_sizes.items():
            for frame in range(n_frames):
                self.prepare_frame(frame)
                image_path = self.export_path / dataset_type / f"r_{frame}.png"
                
                # Render the image
                render_image(image_path)

                # Calculate rotation value
                rotation_value = 360 / 200 * (math.pi / 180)

                # filepath to save
                relative_path = f"./{dataset_type}/r_{frame}"
                # Track camera transform data in the respective dictionary
                transforms_dicts[dataset_type]["frames"].append({
                    "file_path": relative_path,
                    "rotation": rotation_value,
                    "transform_matrix": self.current_camera_transform_matrix
                })
                c_frame += 1
            self.log(f"Finished rendering frames for {dataset_type}")
        
        # Save the camera transform data to json files
        for dataset_type, data in transforms_dicts.items():
            file_path = self.export_path / f"transforms_{dataset_type}.json"
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)
            self.log(f"Saved camera transform data to {file_path}")

        self.write_log()
