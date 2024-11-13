# Usage Documentation for `NerfSyntheticDatasetExporter`

This documentation provides instructions on how to use the `NerfSyntheticDatasetExporter` class to export a synthetic dataset for NeRF-based projects. This exporter class allows you to randomize camera positions around a focus point, align the camera to look at the focus point, and render images with camera transformation data saved for further use.

---

## Class: `NerfSyntheticDatasetExporter`

### Initialization

**Constructor:**
```python
NerfSyntheticDatasetExporter(bpy, export_path: Path, focus_point, distance, dataset_sizes=None)
```

**Parameters:**
- `bpy`: The Blender Python API module.
- `export_path` (Path): The directory where the rendered images and camera transformation data will be saved.
- `focus_point`: The object around which the camera will be positioned. It must have a `location` attribute.
- `distance` (float): The fixed distance from the camera to the focus point.
- `dataset_sizes` (dict, optional): A dictionary specifying the number of frames for "train," "val," and "test" datasets. Default: `{"train": 100, "val": 100, "test": 200}`.

### Attributes

- `self.export_path`: Path to the directory for saving the exported data.
- `self.dataset_sizes`: Dictionary defining the number of images to render for each dataset type.
- `self.scene`: The active Blender scene.
- `self.camera`: The camera object used for rendering.
- `self.camera_positions`: List of randomized camera positions around the focus point.
- `self.log_str`: String to log messages throughout the export process.

---

## Methods

### 1. `set_and_create_export_path(export_path)`
Sets the export path and creates the necessary directory structure for saving images and JSON files.

- **Parameters:**
  - `export_path` (Path): The path where data will be saved.
- **Behavior:**
  - Deletes any existing directory at the path.
  - Creates directories for "train," "val," and "test" datasets.

---

### 2. `randomize_camera_locations()`
Randomizes camera positions around the `focus_point` using spherical coordinates and ensures a fixed distance from the focus point.

- **Behavior:**
  - Generates random positions for the camera while maintaining a consistent distance from the focus point.
  - Stores these positions in `self.camera_positions`.

---

### 3. `prepare_frame(frame_number)`
Moves the camera to a specified position and aligns it to look at the `focus_point`.

- **Parameters:**
  - `frame_number` (int): The frame number to prepare.

---

### 4. `current_camera_transform_matrix` (Property)
Returns the camera's 4x4 transformation matrix in a list format.

---

### 5. `print_info(message)`
Prints an informational message to the Blender console.

- **Parameters:**
  - `message` (str): The message to display.

---

### 6. `log(message)`
Logs a message to the internal log string.

- **Parameters:**
  - `message` (str): The message to log.

---

### 7. `write_log()`
Writes the accumulated log messages to a file named `exporter_log.txt` in the export path.

---

### 8. `test_render()`
Renders a single frame to test the output.

- **Behavior:**
  - Sets the rendering engine to "Cycles."
  - Configures GPU settings and render parameters.
  - Renders an image to "test.png" in the export path.

---

### 9. `render_all()`
Renders all frames for the training, validation, and test datasets and saves the camera transformation data to JSON files.

- **Behavior:**
  - Sets the rendering engine to "Cycles" and configures GPU settings.
  - Renders all frames for each dataset type and logs progress.
  - Saves the camera transform data to `transforms_train.json`, `transforms_val.json`, and `transforms_test.json`.

---

## Usage Example

### Step 1: Initialize the Exporter
```python
import bpy
from pathlib import Path

focus_object = bpy.data.objects['FocusPoint']  # Replace with your focus object
export_path = Path("/path/to/export/directory")
distance = 7.0  # Distance from the camera to the focus point

exporter = NerfSyntheticDatasetExporter(bpy, export_path, focus_object, distance)
```

### Step 2: Test a Single Render
```python
exporter.test_render()
```

### Step 3: Render All Frames and Save Transform Data
```python
exporter.render_all()
```

---

## Notes
- Ensure that your focus object and camera are set up properly in Blender.
- The rendering engine is set to "Cycles," and GPU rendering is used. Make sure your system supports GPU rendering.
- You can modify render settings (e.g., samples, resolution) in the `test_render()` and `render_all()` methods if needed.
- Camera positions are randomized to cover a spherical area around the focus point, ensuring diverse views.

