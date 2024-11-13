import pandas as pd
from plyfile import PlyData
from pathlib import Path
import numpy as np
from typing import List


class PlyWrapper:
    def __init__(self, data):
        # Check if data is provided as a file path or PlyData object
        if isinstance(data, (str, Path)):
            ply_path = Path(data)
            if not ply_path.exists():
                raise FileNotFoundError(f"File not found: {data}")
            self.ply_data = PlyData.read(data)
        elif isinstance(data, PlyData):
            self.ply_data = data
        else:
            raise ValueError("Either ply_path or ply_data must be provided.")
        
        self.capture_data()
        
    def matching_dimensions(self, other: Path):
        # Check if 'other' is a Path object or string path to the PLY file
        if isinstance(other, (str, Path)):
            other_ply_data = PlyData.read(other)  # Read from the file path
        elif isinstance(other, PlyData):
            other_ply_data = other  # Directly use the provided PlyData object
        else:
            raise TypeError("The 'other' parameter must be a file path (str or Path) or a PlyData object.")
        
        matching_dims = {
            "xyz": (
                self.ply_data.elements[0]["x"].count == other_ply_data.elements[0]["x"].count
                and self.ply_data.elements[0]["y"].count == other_ply_data.elements[0]["y"].count
                and self.ply_data.elements[0]["z"].count == other_ply_data.elements[0]["z"].count
            ),
            "opacities": self.ply_data.elements[0]["opacity"].count == other_ply_data.elements[0]["opacity"].count,
            "direct_current": (
                self.ply_data.elements[0]["f_dc_0"].count == other_ply_data.elements[0]["f_dc_0"].count
                and self.ply_data.elements[0]["f_dc_1"].count == other_ply_data.elements[0]["f_dc_1"].count
                and self.ply_data.elements[0]["f_dc_2"].count == other_ply_data.elements[0]["f_dc_2"].count
            ),
        }
        return matching_dims
    
    def get_dims(self):
        return {
            "xyz": self.xyz.shape,
            "opacities": self.opacities.shape,
            "direct_current": self.direct_current.shape,
        }
    
    def capture_data(self):
        self.xyz = np.stack((np.asarray(self.ply_data.elements[0]["x"]),
                             np.asarray(self.ply_data.elements[0]["y"]),
                             np.asarray(self.ply_data.elements[0]["z"])),  axis=1)
        self.opacities = np.asarray(self.ply_data.elements[0]["opacity"])[..., np.newaxis]
        self.direct_current = np.zeros((self.xyz.shape[0], 3, 1))
        self.direct_current[:, 0, 0] = np.asarray(self.ply_data.elements[0]["f_dc_0"])
        self.direct_current[:, 1, 0] = np.asarray(self.ply_data.elements[0]["f_dc_1"])
        self.direct_current[:, 2, 0] = np.asarray(self.ply_data.elements[0]["f_dc_2"])
        self.direct_current = self.direct_current.squeeze()
        
        extra_f_names = [p.name for p in self.ply_data.elements[0].properties if p.name.startswith("f_rest_")]
        extra_f_names = sorted(extra_f_names, key=lambda x: int(x.split('_')[-1]))
        
        self.higher_order_shs = np.zeros((len(self.xyz), len(extra_f_names)))
        for i, f_name in enumerate(extra_f_names):
            self.higher_order_shs[:, i] = np.asarray(self.ply_data.elements[0][f_name])
        
        #self.max_sh_degree = int(extra_f_names[-1].split('_')[-1])
        # assert len(extra_f_names)==3*(self.max_sh_degree + 1) ** 2 - 3
        #features_extra = np.zeros((self.xyz.shape[0], len(extra_f_names)))
        #for idx, attr_name in enumerate(extra_f_names):
        #    features_extra[:, idx] = np.asarray(self.ply_data.elements[0][attr_name])
        # Reshape (P,F*SH_coeffs) to (P, F, SH_coeffs except DC)
        #features_extra = features_extra.reshape((features_extra.shape[0], 3, (self.max_sh_degree + 1) ** 2 - 1))
        #self.higher_order = features_extra

        scale_names = [p.name for p in self.ply_data.elements[0].properties if p.name.startswith("scale_")]
        scale_names = sorted(scale_names, key = lambda x: int(x.split('_')[-1]))
        scales = np.zeros((self.xyz.shape[0], len(scale_names)))
        for idx, attr_name in enumerate(scale_names):
            scales[:, idx] = np.asarray(self.ply_data.elements[0][attr_name])

        rot_names = [p.name for p in self.ply_data.elements[0].properties if p.name.startswith("rot")]
        rot_names = sorted(rot_names, key = lambda x: int(x.split('_')[-1]))
        rots = np.zeros((self.xyz.shape[0], len(rot_names)))
        for idx, attr_name in enumerate(rot_names):
            rots[:, idx] = np.asarray(self.ply_data.elements[0][attr_name])
        
        self.scaling = scales
        self.rotation = rots

    def get_data(self, attrs: List[str] = None):
        if not attrs:
            return {
                "xyz": self.xyz,
                "opacities": self.opacities,
                "direct_current": self.direct_current,
                "higher_order": self.higher_order_shs,
                "scaling": self.scaling,
                "rotation": self.rotation,
            }
        data = {}
        for attr in attrs:
            if hasattr(self, attr):
                data[attr] = getattr(self, attr)
            else:
                raise AttributeError(f"'{attr}' is not a valid attribute of PlyWrapper.")
        return data
    
    """
    returns a pandas dataframe of shape (N, 3) containing the SH coefficients as values and the xyz coordinates in the
    index
    """
    def get_sh_coeffs_standardized_format(self):
        # Flatten XYZ coordinates for the index
        xyz_tuples = [tuple(coord) for coord in self.xyz]
        
        # Concatenate SH coefficients (direct current and higher order)
        # Reshape the SH coefficients into a flat format (if needed)
        sh_coeffs = np.concatenate([self.direct_current, self.higher_order_shs], axis=1)
        
        # Create a pandas DataFrame
        df = pd.DataFrame(sh_coeffs, index=xyz_tuples)
        
        # Name the index columns as x, y, z
        df.index = pd.MultiIndex.from_tuples(df.index, names=["x", "y", "z"])
        
        return df
