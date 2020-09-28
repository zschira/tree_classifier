import rasterio
import pathlib
from data.utils import allowable_site, allowable_data_type
from data.voxel import Voxel
import geopandas as gpd
from liblas import file as las_file
import numpy as np

class Data:
    file_ext = ""

    def __init__(self, base_direc, data_type, site, plot_id, file_ext):
        self.base_direc = pathlib.Path(base_direc).absolute()
        self.data_type = allowable_data_type(data_type)
        self.site = allowable_site(site)
        self.plot_id = plot_id
        self.full_path = self.base_direc / 'train/RemoteSensing/' / self.data_type / "{}_{}.{}".format(self.site, self.plot_id, file_ext)
        self.data = self.open_file()

    def open_file(self):
        return None

class Image(Data):
    def __init__(self, base_direc, data_type, site, plot_id):
        super(Image, self).__init__(base_direc, data_type, site, plot_id, "tif")

    def open_file(self):
        return rasterio.open(self.full_path)

    def as_array(self):
        return self.data.read()

    def as_normalized_array(self):
        array = self.as_array()
        normalized = (array - np.mean(array)) / np.std(array)
        return np.moveaxis(normalized, 0, -1)

    def get_bounds(self):
        return self.data.bounds

class Shapefile():
    def __init__(self, base_direc, site):
        self.base_direc = pathlib.Path(base_direc).absolute()
        self.site = allowable_site(site)
        self.full_path = self.base_direc / 'train/ITC/' / "train_{}.shp".format(self.site)
        self.shape = gpd.read_file(self.full_path)

    def filter(self, left, right, bottom, top):
        return self.shape.cx[left:right, bottom:top]

class PointCloud(Data):
    def __init__(self, base_direc, site, plot_id):
        super(PointCloud, self).__init__(base_direc, "LAS", site, plot_id, "las")

    def open_file(self):
        return las_file.File(self.full_path)

    def as_array(self):
        array = np.zeros((len(self.data), 4))
        for (i, p) in enumerate(self.data):
            array[i, :] = np.array([p.x, p.y, p.z, p.intensity])

        return array

    def to_voxels(self, left, top, grid_size):
        xy_grids = int(20 / grid_size)
        z_grids = int(35 / grid_size)
        points = self.as_array()
        points[:, 3] = self.normalize_intensity(points[:, 3])
        (z_min, points) = self.compute_z_min(points)
        voxel_func = np.vectorize(Voxel)
        voxels = voxel_func(np.zeros((xy_grids, xy_grids, z_grids)))
        for p in points:
            x_ind = int((p[0] - left) / grid_size)
            y_ind = int((top - p[1]) / grid_size)
            z_ind = int((p[2] - z_min) / grid_size)

            # Avoid bad indices
            x_ind = 39 if x_ind == 40 else x_ind
            y_ind = 39 if y_ind == 40 else y_ind
            if z_ind >= z_grids:
                continue

            voxels[x_ind, y_ind, z_ind].append(p[3])

        mean_intensity = np.vectorize(lambda voxel: voxel.mean())
        return mean_intensity(voxels)

    def compute_z_min(self, points):
        z_min = -1
        while z_min == -1:
            z_min = np.amin(points[:, 2])
            if (np.mean(points[:,2]) - z_min) > 20:
                points = points[points[:,2] != z_min, :]
                z_min = -1

        return (z_min, points)

    def normalize_intensity(self, intensity):
        return (intensity - np.mean(intensity)) / np.std(intensity)
